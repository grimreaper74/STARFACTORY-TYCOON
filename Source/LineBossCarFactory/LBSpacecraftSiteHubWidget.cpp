// Copyright Epic Games, Inc. All Rights Reserved.

#include "LBSpacecraftSiteHubWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/Border.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Engine/Texture2D.h"
#include "LBSpacecraftBuildAuthority.h"
#include "LBSpacecraftCommandPanelWidget.h"
#include "LBSpacecraftGameMode.h"
#include "LBSpacecraftPlayerPawn.h"
#include "LBSpacecraftProgressionAuthority.h"

#define LOCTEXT_NAMESPACE "LBSpacecraftSiteHub"

namespace LBSpacecraftSiteHubPrivate
{
	/** The artwork these rectangles were measured against. Recorded so a
	 *  replacement picture at another size is obviously still fine (the
	 *  rectangles are normalised) and a picture with a DIFFERENT LAYOUT
	 *  is obviously not. */
	constexpr float ArtWidthPx = 1672.f;
	constexpr float ArtHeightPx = 941.f;

	FVector2D N(float X, float Y)
	{
		return FVector2D(X / ArtWidthPx, Y / ArtHeightPx);
	}

	FLBSpacecraftHubPlace Make(const TCHAR* Id, FText Name,
		const TCHAR* Definition, float X0, float Y0, float X1, float Y1,
		FVector2D SiteAtCm = FVector2D::ZeroVector,
		int32 RequiredUnlock = -1)
	{
		FLBSpacecraftHubPlace Place;
		Place.PlaceId = FName(Id);
		Place.DisplayName = MoveTemp(Name);
		Place.DefinitionId = Definition != nullptr
			? FName(Definition) : FName();
		Place.SiteAtCm = SiteAtCm;
		Place.RequiredUnlock = RequiredUnlock;
		Place.Min = N(X0, Y0);
		Place.Max = N(X1, Y1);
		return Place;
	}

	/** THE STATE BADGE - a padlock, or a plus.
	 *
	 *  Drawn art now, not four rectangles assembled in code. The first
	 *  version read correctly, which was all it aimed for, but against
	 *  a painted site it looked exactly like what it was.
	 *
	 *  Both are SHAPES, never letters: a padlock and a plus carry no
	 *  language, and no artwork in this game may contain text because
	 *  it ships translated.
	 *
	 *  Centre is NORMALISED over the picture, size is in PIXELS, so a
	 *  badge stays legible at any window size instead of shrinking with
	 *  the building it marks. That is what point anchors are for. */
	/** A small dark chip of text on the picture - the enter and buy
	 *  captions. Text, not a baked icon, so it localises. */
	void AddCaption(UWidgetTree& Tree, UCanvasPanel& Canvas,
		const FVector2D& Centre, const FString& Text)
	{
		UBorder* Chip = Tree.ConstructWidget<UBorder>(UBorder::StaticClass());
		Chip->SetBrushColor(FLinearColor(0.106f, 0.106f, 0.106f, 0.88f));
		Chip->SetPadding(FMargin(8.f, 3.f));
		UTextBlock* Label = Tree.ConstructWidget<UTextBlock>(
			UTextBlock::StaticClass());
		Label->SetText(FText::FromString(Text));
		Label->SetColorAndOpacity(FSlateColor(
			FLinearColor(0.93f, 0.93f, 0.92f, 1.f)));
		FSlateFontInfo Font = Label->GetFont();
		Font.Size = 13;
		Label->SetFont(Font);
		Chip->SetContent(Label);
		if (UCanvasPanelSlot* CanvasSlot = Canvas.AddChildToCanvas(Chip))
		{
			CanvasSlot->SetAnchors(FAnchors(Centre.X, Centre.Y,
				Centre.X, Centre.Y));
			CanvasSlot->SetAlignment(FVector2D(0.5f, 0.5f));
			CanvasSlot->SetPosition(FVector2D::ZeroVector);
			CanvasSlot->SetAutoSize(true);
			CanvasSlot->SetZOrder(31);
		}
	}

	void AddStateBadge(UWidgetTree& Tree, UCanvasPanel& Canvas,
		const FVector2D& Centre, float SizePx, const TCHAR* IconPath)
	{
		UTexture2D* Icon = LoadObject<UTexture2D>(nullptr, IconPath);
		if (Icon == nullptr)
		{
			UE_LOG(LogTemp, Warning,
				TEXT("SPACECRAFT HUB: badge %s did not load - the place "
					"will show no state at all"), IconPath);
			return;
		}
		UImage* Img = Tree.ConstructWidget<UImage>(UImage::StaticClass());
		Img->SetBrushFromTexture(Icon, false);
		if (UCanvasPanelSlot* CanvasSlot = Canvas.AddChildToCanvas(Img))
		{
			CanvasSlot->SetAnchors(FAnchors(Centre.X, Centre.Y,
				Centre.X, Centre.Y));
			CanvasSlot->SetAlignment(FVector2D(0.5f, 0.5f));
			CanvasSlot->SetPosition(FVector2D::ZeroVector);
			CanvasSlot->SetSize(FVector2D(SizePx, SizePx));
			CanvasSlot->SetZOrder(30);
		}
	}
}

ULBSpacecraftSiteHubWidget::ULBSpacecraftSiteHubWidget(
	const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	// SELF-HIT-TEST-INVISIBLE, NOT COLLAPSED. A collapsed widget does
	// not tick, so a widget that collapses itself in its constructor can
	// never run the tick that would show it again - it is invisible
	// forever and nothing says why. The widget therefore stays "visible"
	// and passes clicks through itself; what actually shows and hides is
	// the root canvas, whose children carry the hit testing.
	SetVisibility(ESlateVisibility::SelfHitTestInvisible);
}

const TArray<FLBSpacecraftHubPlace>&
ULBSpacecraftSiteHubWidget::Places()
{
	using namespace LBSpacecraftSiteHubPrivate;
	// MEASURED OFF THE LABELLED REFERENCE the artist supplied beside the
	// clean scene, then verified by drawing the rectangles back over the
	// clean picture and looking at them. Two overlap - the operations
	// building sits in front of the test hall - and that is resolved by
	// smallest-wins in PlaceAt rather than by fudging the boxes.
	static const TArray<FLBSpacecraftHubPlace> Table = {
		// MEASURED OFF v006 and verified by drawing the rectangles back
		// over the picture with the interface keep-out zones marked, so
		// occlusion is seen rather than assumed.
		//
		// RE-MEASURED, NOT CARRIED OVER. v006 was asked for only as a
		// re-export at full resolution - the previous delivery had two
		// frames stacked in one canvas, halving each one's height - but
		// what came back was a fresh generation with the site sitting
		// higher and further left. Reusing the old numbers would have
		// put the research lab hotspot on bare ground. A picture that
		// is "the same but sharper" still has to be measured again.
		Make(TEXT("ShipFactory"),
			LOCTEXT("HubShipFactory", "Ship factory"),
			TEXT("ShipFactoryHall"),     500.f, 265.f,  770.f, 475.f),
		Make(TEXT("PartsFactory"),
			LOCTEXT("HubPartsFactory", "Parts factory"),
			TEXT("SubAssemblyHall"),     805.f, 290.f, 1030.f, 475.f,
			FVector2D(-15500.f, 15500.f),
			static_cast<int32>(ELBSpacecraftUnlock::Fabrication)),
		Make(TEXT("PowerPlant"),
			LOCTEXT("HubPowerPlant", "Power plant"),
			TEXT("PowerStation"),       1055.f, 295.f, 1325.f, 485.f,
			FVector2D(15500.f, -15500.f)),
		Make(TEXT("ReceivingDock"),
			LOCTEXT("HubReceivingDock", "Receiving dock"),
			nullptr,                     550.f, 115.f,  760.f, 235.f),
		Make(TEXT("StorageWarehouse"),
			LOCTEXT("HubStorage", "Storage warehouse"),
			nullptr,                     785.f,  70.f, 1015.f, 275.f),
		Make(TEXT("DroneDepot"),
			LOCTEXT("HubDroneDepot", "Drone depot"),
			nullptr,                    1040.f, 130.f, 1220.f, 260.f),
		// THE APRON IS WHERE FINISHED CRAFT PARK. They fly out of the
		// ship factory itself, so there is no launch facility here.
		Make(TEXT("ParkingApron"),
			LOCTEXT("HubParkingApron", "Parking apron"),
			nullptr,                    1350.f, 265.f, 1655.f, 505.f),
		Make(TEXT("ResearchLab"),
			LOCTEXT("HubResearchLab", "Research lab"),
			nullptr,                     455.f, 505.f,  630.f, 665.f),
		Make(TEXT("TestHall"),
			LOCTEXT("HubTestHall", "Test hall"),
			nullptr,                     645.f, 475.f,  835.f, 635.f),
		Make(TEXT("Operations"),
			LOCTEXT("HubOperations", "Operations building"),
			nullptr,                     795.f, 585.f,  950.f, 735.f),
		Make(TEXT("MaterialsRefinery"),
			LOCTEXT("HubRefinery", "Materials refinery"),
			nullptr,                     920.f, 455.f, 1135.f, 695.f),
		Make(TEXT("HeavyShipFactory"),
			LOCTEXT("HubHeavyShipFactory", "Heavy ship factory"),
			nullptr,                    1140.f, 500.f, 1445.f, 735.f),
	};
	return Table;
}

FName ULBSpacecraftSiteHubWidget::PlaceAt(const FVector2D& Point)
{
	FName Best;
	double BestArea = TNumericLimits<double>::Max();
	for (const FLBSpacecraftHubPlace& Place : Places())
	{
		if (Point.X < Place.Min.X || Point.X > Place.Max.X
			|| Point.Y < Place.Min.Y || Point.Y > Place.Max.Y)
		{
			continue;
		}
		// SMALLEST WINS. The operations building is drawn in front of
		// the test hall and their rectangles overlap; without this the
		// bigger building would swallow every click in the overlap and
		// the small one would be unclickable.
		const double Area = (Place.Max.X - Place.Min.X)
			* (Place.Max.Y - Place.Min.Y);
		if (Area < BestArea)
		{
			BestArea = Area;
			Best = Place.PlaceId;
		}
	}
	return Best;
}

void ULBSpacecraftSiteHubWidget::BindGame(ALBSpacecraftGameMode* InGameMode)
{
	GameMode = InGameMode;
	OpenSignature.Reset();
}

ULBSpacecraftSiteHubWidget::EState
ULBSpacecraftSiteHubWidget::StateOf(FName PlaceId) const
{
	const FLBSpacecraftHubPlace* Place = Places().FindByPredicate(
		[PlaceId](const FLBSpacecraftHubPlace& P)
		{ return P.PlaceId == PlaceId; });
	if (Place == nullptr || Place->DefinitionId.IsNone())
	{
		return EState::Locked;
	}
	if (IsPlaceOpen(PlaceId))
	{
		return EState::Open;
	}
	if (Place->SiteAtCm.IsNearlyZero())
	{
		return EState::Locked;
	}
	// A MILESTONE STILL TO COME PADLOCKS. The parts factory exists in
	// the catalogue and has a spot waiting, but on-site fabrication
	// unlocks after two deliveries - so a plus would invite a click
	// that can only be refused. The refusal still names the milestone
	// when clicked, which is where the player learns the goal.
	if (Place->RequiredUnlock >= 0)
	{
		const ALBSpacecraftProgressionAuthority* Progression =
			GameMode != nullptr ? GameMode->GetProgression() : nullptr;
		if (Progression == nullptr || !Progression->IsUnlocked(
			static_cast<ELBSpacecraftUnlock>(Place->RequiredUnlock)))
		{
			return EState::Locked;
		}
	}
	// The game HAS this building, the player can build it, and it is
	// not built. That is an invitation, not a locked door.
	return EState::Buildable;
}

bool ULBSpacecraftSiteHubWidget::IsPlaceOpen(FName PlaceId) const
{
	const FLBSpacecraftHubPlace* Place = Places().FindByPredicate(
		[PlaceId](const FLBSpacecraftHubPlace& P)
		{ return P.PlaceId == PlaceId; });
	if (Place == nullptr || Place->DefinitionId.IsNone()
		|| GameMode == nullptr || GameMode->GetBuildAuthority() == nullptr)
	{
		return false;
	}
	for (const FLBSpacecraftStationRecord& Record :
		GameMode->GetBuildAuthority()->GetStations())
	{
		if (Record.DefinitionId == Place->DefinitionId)
		{
			return true;
		}
	}
	return false;
}

FString ULBSpacecraftSiteHubWidget::EnterPlace(FName PlaceId)
{
	const FLBSpacecraftHubPlace* Place = Places().FindByPredicate(
		[PlaceId](const FLBSpacecraftHubPlace& P)
		{ return P.PlaceId == PlaceId; });
	if (Place == nullptr)
	{
		return TEXT("NOWHERE THERE");
	}
	const FString Name = Place->DisplayName.ToString().ToUpper();
	// EVERY REFUSAL NAMES ITSELF, like every other refusal in this game.
	if (Place->DefinitionId.IsNone())
	{
		return FString::Printf(
			TEXT("%s IS NOT IN THE GAME YET - IT IS DRAWN SO YOU CAN SEE "
				"WHERE IT WILL STAND"), *Name);
	}
	if (GameMode == nullptr || GameMode->GetBuildAuthority() == nullptr)
	{
		return TEXT("NO SITE TO ENTER");
	}
	FName Station;
	for (const FLBSpacecraftStationRecord& Record :
		GameMode->GetBuildAuthority()->GetStations())
	{
		if (Record.DefinitionId == Place->DefinitionId)
		{
			Station = Record.StationId;
			break;
		}
	}
	if (Station.IsNone())
	{
		// BUILD IT FROM HERE. The panel's build button arms a placement
		// cursor for the player to click in the world, which makes no
		// sense on a picture: the site layout is fixed, so the place
		// already knows where its building stands. Everything else -
		// cost, power, progression, legality - goes through the normal
		// powered placement and fails closed with its own reason.
		if (Place->SiteAtCm.IsNearlyZero()
			|| GameMode->GetPowerAuthority() == nullptr
			|| GameMode->GetInventoryAuthority() == nullptr)
		{
			return FString::Printf(
				TEXT("%s IS NOT BUILT YET"), *Name);
		}
		// QUOTE FIRST, BUY SECOND. The picture has no ghost, no price
		// and no cancel; one click spending a fifth of the opening
		// bankroll was the stranger playthrough's worst moment.
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(Place->DefinitionId);
		const double Now = FPlatformTime::Seconds();
		if (PendingBuyPlace != PlaceId || Now - PendingBuyStamp > 8.0)
		{
			PendingBuyPlace = PlaceId;
			PendingBuyStamp = Now;
			const int64 Credits = Definition != nullptr
				? Definition->CostPence / 100 : 0;
			return FString::Printf(
				TEXT("BUY %s FOR %s CR? CLICK IT AGAIN TO CONFIRM"), *Name,
				*FText::AsNumber(Credits).ToString());
		}
		PendingBuyPlace = NAME_None;
		FString BuildReason;
		FName Placed;
		const bool bBuilt = ALBSpacecraftGameMode::PlaceStationPowered(
			*GameMode->GetBuildAuthority(),
			*GameMode->GetPowerAuthority(),
			*GameMode->GetInventoryAuthority(), Place->DefinitionId,
			FTransform(FRotator::ZeroRotator,
				FVector(Place->SiteAtCm.X, Place->SiteAtCm.Y, 0.f)),
			Placed, BuildReason, GameMode->GetProductionAuthority(),
			GameMode->GetProgression());
		if (!bBuilt)
		{
			return FString::Printf(TEXT("CANNOT BUILD %s: %s"), *Name,
				*BuildReason);
		}
		OpenSignature.Reset();
		return FString::Printf(TEXT("BUILT %s - CLICK IT AGAIN TO GO IN"),
			*Name);
	}
	APlayerController* Controller = GetOwningPlayer();
	ALBSpacecraftPlayerPawn* Pawn = Controller != nullptr
		? Cast<ALBSpacecraftPlayerPawn>(Controller->GetPawn()) : nullptr;
	if (Pawn == nullptr)
	{
		return TEXT("NO PAWN TO MOVE");
	}
	Pawn->SetSelectedStation(Station);
	Pawn->FocusStation(Station);
	if (Root != nullptr)
	{
		Root->SetVisibility(ESlateVisibility::Collapsed);
	}
	return FString::Printf(TEXT("ENTERED %s"), *Name);
}

TSharedRef<SWidget> ULBSpacecraftSiteHubWidget::RebuildWidget()
{
	if (Root == nullptr)
	{
		Root = WidgetTree->ConstructWidget<UCanvasPanel>(
			UCanvasPanel::StaticClass(), FName(TEXT("SiteHubRoot")));
		WidgetTree->RootWidget = Root;
	}
	RebuildContent();
	return Super::RebuildWidget();
}

void ULBSpacecraftSiteHubWidget::RebuildContent()
{
	using namespace LBSpacecraftSiteHubPrivate;
	if (Root == nullptr)
	{
		return;
	}
	Root->ClearChildren();

	// THE PICTURE, full bleed. The artwork is 1672x941, which is 16:9 to
	// within a pixel, so filling the screen costs no visible distortion
	// and keeps every hotspot anchor exactly where it was measured.
	UImage* Scene = WidgetTree->ConstructWidget<UImage>(
		UImage::StaticClass(), FName(TEXT("SiteHubScene")));
	if (UTexture2D* Art = LoadObject<UTexture2D>(nullptr,
		TEXT("/Game/LineBoss/UI/SiteHub/T_LB_SiteHub_v006")
		TEXT(".T_LB_SiteHub_v006")))
	{
		Scene->SetBrushFromTexture(Art, false);
	}
	else
	{
		// SAY SO. A missing picture would otherwise leave a blank screen
		// with twelve invisible buttons on it - the same silent-nothing
		// that shipped a hall with no walls this morning.
		UE_LOG(LogTemp, Warning,
			TEXT("SPACECRAFT HUB: the site picture did not load - the "
				"screen will be blank. Check the texture is cooked."));
	}
	if (UCanvasPanelSlot* CanvasSlot = Root->AddChildToCanvas(Scene))
	{
		CanvasSlot->SetAnchors(FAnchors(0.f, 0.f, 1.f, 1.f));
		CanvasSlot->SetOffsets(FMargin(0.f));
		CanvasSlot->SetZOrder(0);
	}

	for (const FLBSpacecraftHubPlace& Place : Places())
	{
		const FName PlaceId = Place.PlaceId;
		const EState State = StateOf(PlaceId);

		// The project's own tagged button, so the place id travels with
		// the click instead of needing a dispatcher per hotspot.
		ULBSpacecraftTaggedButton* Hit =
			WidgetTree->ConstructWidget<ULBSpacecraftTaggedButton>(
				ULBSpacecraftTaggedButton::StaticClass(),
				FName(*FString::Printf(TEXT("Hub_%s"),
					*Place.PlaceId.ToString())));
		Hit->Tag = PlaceId;
		Hit->OnTagClicked = [this](FName Clicked)
		{
			const FString Said = EnterPlace(Clicked);
			if (StatusText != nullptr)
			{
				StatusText->SetText(FText::FromString(Said));
			}
			// Through the toast the player already reads: the hub's own
			// strip sat on beige ground in pale text and was wiped by
			// the rebuild a purchase triggers (stranger playthrough,
			// 2026-09-02 - every hub message went to the log only).
			if (APlayerController* Owner = GetOwningPlayer())
			{
				if (ALBSpacecraftPlayerPawn* OwnerPawn =
					Cast<ALBSpacecraftPlayerPawn>(Owner->GetPawn()))
				{
					OwnerPawn->SetLastActionText(Said);
				}
			}
			UE_LOG(LogTemp, Display, TEXT("SPACECRAFT HUB: %s"), *Said);
		};
		Hit->Arm();
		FButtonStyle Style = Hit->GetStyle();
		const FLinearColor Clear(0.f, 0.f, 0.f, 0.f);
		Style.Normal.TintColor = FSlateColor(Clear);
		Style.Hovered.TintColor = FSlateColor(
			FLinearColor(0.75f, 0.89f, 1.f, 0.16f));
		Style.Pressed.TintColor = FSlateColor(
			FLinearColor(0.75f, 0.89f, 1.f, 0.28f));
		Style.Disabled.TintColor = FSlateColor(Clear);
		Hit->SetStyle(Style);
		if (UCanvasPanelSlot* CanvasSlot = Root->AddChildToCanvas(Hit))
		{
			CanvasSlot->SetAnchors(FAnchors(Place.Min.X, Place.Min.Y,
				Place.Max.X, Place.Max.Y));
			CanvasSlot->SetOffsets(FMargin(0.f));
			CanvasSlot->SetZOrder(20);
		}
		// WHAT THE CLICK DOES, written on the picture. The stranger
		// playthrough found the player's own factory was the only place
		// with NO mark, and the "+" gave no price.
		{
			FString Caption;
			if (State == EState::Open)
			{
				bool bBuilt = false;
				if (GameMode != nullptr
					&& GameMode->GetBuildAuthority() != nullptr)
				{
					for (const FLBSpacecraftStationRecord& Record :
						GameMode->GetBuildAuthority()->GetStations())
					{
						bBuilt |= !Place.DefinitionId.IsNone()
							&& Record.DefinitionId == Place.DefinitionId;
					}
				}
				if (bBuilt)
				{
					Caption = LOCTEXT("HubEnter", "ENTER").ToString();
				}
			}
			else if (State == EState::Buildable)
			{
				const FLBSpacecraftStationDefinition* Definition =
					ALBSpacecraftBuildAuthority::FindDefinition(
						Place.DefinitionId);
				if (Definition != nullptr)
				{
					Caption = FText::Format(LOCTEXT("HubBuy", "BUY  {0} cr"),
						FText::AsNumber(Definition->CostPence / 100))
						.ToString();
				}
			}
			if (!Caption.IsEmpty())
			{
				AddCaption(*WidgetTree, *Root,
					FVector2D((Place.Min.X + Place.Max.X) * 0.5f,
						(Place.Min.Y + Place.Max.Y) * 0.5f + 0.045f),
					Caption);
			}
		}
		if (State != EState::Open)
		{
			AddStateBadge(*WidgetTree, *Root,
				FVector2D((Place.Min.X + Place.Max.X) * 0.5f,
					(Place.Min.Y + Place.Max.Y) * 0.5f), 42.f,
				State == EState::Buildable
					? TEXT("/Game/LineBoss/UI/SiteHub/")
						TEXT("T_LB_Icon_HubBuild_v001")
						TEXT(".T_LB_Icon_HubBuild_v001")
					: TEXT("/Game/LineBoss/UI/SiteHub/")
						TEXT("T_LB_Icon_HubLocked_v001")
						TEXT(".T_LB_Icon_HubLocked_v001"));
		}
	}

	StatusText = WidgetTree->ConstructWidget<UTextBlock>(
		UTextBlock::StaticClass(), FName(TEXT("SiteHubStatus")));
	StatusText->SetColorAndOpacity(FSlateColor(
		FLinearColor(0.93f, 0.93f, 0.92f, 1.f)));
	if (UCanvasPanelSlot* CanvasSlot = Root->AddChildToCanvas(StatusText))
	{
		CanvasSlot->SetAnchors(FAnchors(0.02f, 0.94f, 0.98f, 0.99f));
		CanvasSlot->SetOffsets(FMargin(0.f));
		CanvasSlot->SetZOrder(40);
	}
}

void ULBSpacecraftSiteHubWidget::NativeTick(const FGeometry& MyGeometry,
	float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	APlayerController* Controller = GetOwningPlayer();
	ALBSpacecraftPlayerPawn* Pawn = Controller != nullptr
		? Cast<ALBSpacecraftPlayerPawn>(Controller->GetPawn()) : nullptr;
	const bool bShow = Pawn != nullptr && Pawn->IsSiteMapView();
	if (Root != nullptr)
	{
		Root->SetVisibility(bShow ? ESlateVisibility::Visible
			: ESlateVisibility::Collapsed);
	}
	if (!bShow)
	{
		return;
	}
	// Rebuild only when what is OPEN changes - building a parts factory
	// unlocks a place, and nothing else about this screen moves.
	FString Signature;
	for (const FLBSpacecraftHubPlace& Place : Places())
	{
		Signature += IsPlaceOpen(Place.PlaceId) ? TEXT("1") : TEXT("0");
	}
	if (Signature != OpenSignature)
	{
		OpenSignature = Signature;
		RebuildContent();
	}
}

#undef LOCTEXT_NAMESPACE
