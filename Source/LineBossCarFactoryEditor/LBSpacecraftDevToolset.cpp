#include "LBSpacecraftDevToolset.h"

#include "Dom/JsonObject.h"
#include "Editor.h"
#include "Engine/World.h"
#include "Framework/Application/SlateApplication.h"
#include "Framework/Application/SlateUser.h"
#include "GenericPlatform/GenericWindow.h"
#include "Input/Events.h"
#include "Input/HittestGrid.h"
#include "Layout/WidgetPath.h"
#include "InputCoreTypes.h"
#include "Slate/SceneViewport.h"
#include "TimerManager.h"
#include "Widgets/SViewport.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/SWindow.h"
#include "Settings/LevelEditorPlaySettings.h"
#include "LBSpacecraftBuildAuthority.h"
#include "LBSpacecraftGameMode.h"
#include "LBSpacecraftInventoryAuthority.h"
#include "LBSpacecraftPowerAuthority.h"
#include "LBSpacecraftProductionAuthority.h"
#include "LBSpacecraftProgressionAuthority.h"
#include "LBSpacecraftRuntimeCoordinator.h"
#include "LBSpacecraftTrackAuthority.h"
#include "Modules/ModuleManager.h"
#include "Policies/CondensedJsonPrintPolicy.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "ToolsetRegistry/UToolsetRegistry.h"

namespace LBSpacecraftDevToolsetPrivate
{
	FString WriteJson(const TSharedRef<FJsonObject>& Root)
	{
		FString Out;
		const TSharedRef<TJsonWriter<TCHAR,
			TCondensedJsonPrintPolicy<TCHAR>>> Writer =
			TJsonWriterFactory<TCHAR,
				TCondensedJsonPrintPolicy<TCHAR>>::Create(&Out);
		FJsonSerializer::Serialize(Root, Writer);
		return Out;
	}

	FString FailJson(const FString& Error)
	{
		const TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
		Root->SetBoolField(TEXT("success"), false);
		Root->SetStringField(TEXT("error"), Error);
		return WriteJson(Root);
	}

	/** The live PIE/game world, or null. The authorities only exist in
	 *  a playing world - the edited level has none. */
	UWorld* FindPlayWorld()
	{
		return GEditor != nullptr ? GEditor->PlayWorld : nullptr;
	}

	FString EnumName(const UEnum* Enum, int64 Value)
	{
		return Enum != nullptr
			? Enum->GetNameStringByValue(Value) : FString::FromInt(Value);
	}
}

FString ULBSpacecraftDevToolset::GetSpacecraftFactoryStatus()
{
	using namespace LBSpacecraftDevToolsetPrivate;
	UWorld* World = FindPlayWorld();
	if (World == nullptr)
	{
		return FailJson(TEXT("No PIE session is running - the factory "
			"authorities only exist in a playing world. Start PIE first."));
	}
	ALBSpacecraftGameMode* GameMode =
		ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr)
	{
		return FailJson(TEXT("The PIE world has no spacecraft game mode "
			"(wrong map?)."));
	}
	const TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetBoolField(TEXT("success"), true);

	if (ALBSpacecraftProductionAuthority* Production =
		GameMode->GetProductionAuthority())
	{
		Root->SetNumberField(TEXT("cashPence"),
			static_cast<double>(Production->GetCashPence()));
		Root->SetNumberField(TEXT("stockedCraft"),
			Production->GetStockedCraftCount());
		const UEnum* StageEnum = StaticEnum<ELBSpacecraftStage>();
		TArray<TSharedPtr<FJsonValue>> Units;
		for (const FLBSpacecraftUnitState& Unit : Production->GetUnits())
		{
			const TSharedRef<FJsonObject> U = MakeShared<FJsonObject>();
			U->SetStringField(TEXT("unitId"), Unit.UnitId.ToString());
			U->SetStringField(TEXT("recipeId"), Unit.RecipeId.ToString());
			U->SetStringField(TEXT("stage"),
				EnumName(StageEnum, static_cast<int64>(Unit.Stage)));
			U->SetNumberField(TEXT("producedComponents"),
				Unit.ProducedComponents.Num());
			U->SetNumberField(TEXT("defectPoints"), Unit.DefectPoints);
			U->SetNumberField(TEXT("reworkSecondsRemaining"),
				Unit.ReworkSecondsRemaining);
			U->SetBoolField(TEXT("completed"), Unit.bCompleted);
			U->SetBoolField(TEXT("awaitingSale"), Unit.bAwaitingSale);
			Units.Add(MakeShared<FJsonValueObject>(U));
		}
		Root->SetArrayField(TEXT("units"), Units);
		const UEnum* ContractEnum = StaticEnum<ELBSpacecraftContractState>();
		TArray<TSharedPtr<FJsonValue>> Contracts;
		for (const FLBSpacecraftContract& Contract :
			Production->GetContracts())
		{
			const TSharedRef<FJsonObject> C = MakeShared<FJsonObject>();
			C->SetStringField(TEXT("contractId"),
				Contract.ContractId.ToString());
			C->SetStringField(TEXT("recipeId"),
				Contract.RecipeId.ToString());
			C->SetStringField(TEXT("state"), EnumName(ContractEnum,
				static_cast<int64>(Contract.State)));
			C->SetNumberField(TEXT("quantity"), Contract.Quantity);
			C->SetNumberField(TEXT("dispatched"), Contract.DispatchedCount);
			C->SetNumberField(TEXT("pricePerUnitPence"),
				static_cast<double>(Contract.PricePerUnitPence));
			Contracts.Add(MakeShared<FJsonValueObject>(C));
		}
		Root->SetArrayField(TEXT("contracts"), Contracts);
	}
	if (ALBSpacecraftBuildAuthority* Build = GameMode->GetBuildAuthority())
	{
		Root->SetBoolField(TEXT("commissioned"), Build->IsCommissioned());
		TArray<TSharedPtr<FJsonValue>> Stations;
		for (const FLBSpacecraftStationRecord& Record :
			Build->GetStations())
		{
			const TSharedRef<FJsonObject> S = MakeShared<FJsonObject>();
			S->SetStringField(TEXT("stationId"),
				Record.StationId.ToString());
			S->SetStringField(TEXT("definitionId"),
				Record.DefinitionId.ToString());
			S->SetNumberField(TEXT("drones"),
				Record.InstalledDroneTypes.Num());
			Stations.Add(MakeShared<FJsonValueObject>(S));
		}
		Root->SetArrayField(TEXT("stations"), Stations);
	}
	// Every store with its stacks: the 2026-09-02 stranger run needed
	// "what is actually at the dock" twice and the status print only
	// gave unit totals.
	if (const ALBSpacecraftInventoryAuthority* Inventory =
		GameMode->GetInventoryAuthority())
	{
		TArray<TSharedPtr<FJsonValue>> Stores;
		for (const FName& StoreId : Inventory->GetStoreIds())
		{
			const TSharedRef<FJsonObject> Store = MakeShared<FJsonObject>();
			Store->SetStringField(TEXT("storeId"), StoreId.ToString());
			Store->SetNumberField(TEXT("usedUnits"),
				Inventory->GetUsedUnits(StoreId));
			Store->SetNumberField(TEXT("capacityUnits"),
				Inventory->GetCapacityUnits(StoreId));
			TArray<TSharedPtr<FJsonValue>> Stacks;
			// Through the public quantity query per catalogue item; the
			// stack list itself is the authority's private state.
			for (const FLBSpacecraftItemDefinition& Item :
				FLBSpacecraftItemCatalogue::GetItemTable())
			{
				const int32 Count =
					Inventory->GetQuantity(StoreId, Item.ItemId);
				if (Count <= 0)
				{
					continue;
				}
				const TSharedRef<FJsonObject> Entry =
					MakeShared<FJsonObject>();
				Entry->SetStringField(TEXT("itemId"),
					Item.ItemId.ToString());
				Entry->SetNumberField(TEXT("count"), Count);
				Stacks.Add(MakeShared<FJsonValueObject>(Entry));
			}
			Store->SetArrayField(TEXT("stacks"), Stacks);
			Stores.Add(MakeShared<FJsonValueObject>(Store));
		}
		Root->SetArrayField(TEXT("stores"), Stores);
	}
	if (ALBSpacecraftRuntimeCoordinator* Coordinator =
		GameMode->GetCoordinator())
	{
		Root->SetBoolField(TEXT("configured"), Coordinator->IsConfigured());
		Root->SetStringField(TEXT("lastStartRefusal"),
			Coordinator->GetLastStartRefusal());
		TArray<TSharedPtr<FJsonValue>> Route;
		for (const FLBSpacecraftRouteStep& Step : Coordinator->GetRoute())
		{
			Route.Add(MakeShared<FJsonValueString>(
				Step.StationId.ToString()));
		}
		Root->SetArrayField(TEXT("route"), Route);
	}
	// The running factory's own complaint (stalls, starved stations) -
	// what the toast shows when the player has not just acted.
	Root->SetStringField(TEXT("simAlert"), GameMode->GetSimAlert());
	if (ALBSpacecraftTrackAuthority* Track = GameMode->GetTrackAuthority())
	{
		Root->SetNumberField(TEXT("trackPieces"),
			Track->GetPieces().Num());
	}
	if (ALBSpacecraftPowerAuthority* Power = GameMode->GetPowerAuthority())
	{
		Root->SetNumberField(TEXT("powerDrawKw"), Power->GetTotalDrawKw());
		Root->SetNumberField(TEXT("powerSupplyKw"),
			Power->GetTotalSupplyKw());
	}
	if (ALBSpacecraftProgressionAuthority* Progress =
		GameMode->GetProgression())
	{
		Root->SetNumberField(TEXT("creditedDeliveries"),
			Progress->GetCreditedDeliveries());
		Root->SetNumberField(TEXT("ownedBays"),
			Progress->GetOwnedBayCount());
	}
	return WriteJson(Root);
}

FString ULBSpacecraftDevToolset::RunSpacecraftConsoleCommand(
	const FString& Command)
{
	using namespace LBSpacecraftDevToolsetPrivate;
	UWorld* World = FindPlayWorld();
	if (World == nullptr)
	{
		return FailJson(TEXT("No PIE session is running. Start PIE, then "
			"drive it with the LB.* commands."));
	}
	if (Command.TrimStartAndEnd().IsEmpty())
	{
		return FailJson(TEXT("Empty command."));
	}
	const bool bHandled = GEngine != nullptr
		&& GEngine->Exec(World, *Command);
	const TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetBoolField(TEXT("success"), true);
	Root->SetStringField(TEXT("command"), Command);
	Root->SetBoolField(TEXT("handled"), bHandled);
	return WriteJson(Root);
}

// ---------------------------------------------------------------------
// Synthetic PIE input. Everything goes through FSlateApplication's
// Process* entry points - the exact path a real mouse and keyboard take
// once the OS has delivered them - so UMG buttons, the floor click,
// the placement ghost and the pawn's input mappings all see it. The OS
// cursor is never moved and no window is brought to the front, which
// is the whole point: the first attempt at a stranger playthrough used
// Win32 SendInput and captured the owner's browser instead.
// ---------------------------------------------------------------------
namespace LBSpacecraftDevToolsetPrivate
{
	TSharedPtr<SViewport> FindPieViewportWidget()
	{
		// GetPIEViewport hands back the base FViewport; a PIE viewport is
		// always the Slate-backed FSceneViewport underneath.
		FSceneViewport* Viewport = GEditor != nullptr
			? static_cast<FSceneViewport*>(GEditor->GetPIEViewport())
			: nullptr;
		return Viewport != nullptr ? Viewport->GetViewportWidget().Pin()
			: TSharedPtr<SViewport>();
	}

	FString NoViewportJson()
	{
		return FailJson(TEXT("No PIE viewport - start PIE first (the "
			"EditorAppToolset StartPIE tool), then call again."));
	}

	FKey ButtonKey(const FString& Button)
	{
		if (Button.Equals(TEXT("Right"), ESearchCase::IgnoreCase))
		{
			return EKeys::RightMouseButton;
		}
		if (Button.Equals(TEXT("Middle"), ESearchCase::IgnoreCase))
		{
			return EKeys::MiddleMouseButton;
		}
		return EKeys::LeftMouseButton;
	}

	/** Viewport-local Slate units -> Slate absolute (desktop) units. */
	FVector2D ToAbsolute(const TSharedRef<SViewport>& Widget, float X,
		float Y)
	{
		return Widget->GetCachedGeometry().LocalToAbsolute(FVector2D(X, Y));
	}

	void FocusViewport(const TSharedRef<SViewport>& Widget)
	{
		FSlateApplication::Get().SetAllUserFocus(Widget,
			EFocusCause::SetDirectly);
	}

	/** The widget path under an absolute position, built from the PIE
	 *  window's own hit-test grid. FSlateApplication::ProcessMouseButton*
	 *  consults the REAL OS cursor to pick the window, so with a person's
	 *  mouse elsewhere a synthetic press is silently dropped (hover
	 *  worked, clicks did not - first playthrough attempt). Routing to
	 *  a path we locate ourselves sidesteps that entirely. */
	FWidgetPath PathUnder(const TSharedRef<SViewport>& Widget,
		const FVector2D& Abs)
	{
		TSharedPtr<SWindow> Window =
			FSlateApplication::Get().FindWidgetWindow(Widget);
		if (!Window.IsValid())
		{
			return FWidgetPath();
		}
		TArray<FWidgetAndPointer> Bubble = Window->GetHittestGrid()
			.GetBubblePath(Abs, FSlateApplication::Get().GetCursorRadius(),
				false, 0);
		return FWidgetPath(Bubble);
	}
}

FString ULBSpacecraftDevToolset::GetPieViewportInfo()
{
	using namespace LBSpacecraftDevToolsetPrivate;
	TSharedPtr<SViewport> Widget = FindPieViewportWidget();
	if (!Widget.IsValid())
	{
		return NoViewportJson();
	}
	const FGeometry& Geo = Widget->GetCachedGeometry();
	const TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetBoolField(TEXT("success"), true);
	Root->SetNumberField(TEXT("localWidth"), Geo.GetLocalSize().X);
	Root->SetNumberField(TEXT("localHeight"), Geo.GetLocalSize().Y);
	Root->SetNumberField(TEXT("dpiScale"), Geo.Scale);
	Root->SetNumberField(TEXT("absoluteX"), Geo.GetAbsolutePosition().X);
	Root->SetNumberField(TEXT("absoluteY"), Geo.GetAbsolutePosition().Y);
	return WriteJson(Root);
}

namespace LBSpacecraftDevToolsetPrivate
{
	/** First text found under a widget, depth-first (a button's label). */
	FString FirstTextUnder(const TSharedRef<SWidget>& Widget, int32 Depth)
	{
		if (Widget->GetTypeAsString() == TEXT("STextBlock"))
		{
			return StaticCastSharedRef<STextBlock>(Widget)->GetText()
				.ToString();
		}
		if (Depth > 8)
		{
			return FString();
		}
		FChildren* Children = Widget->GetChildren();
		if (Children == nullptr)
		{
			return FString();
		}
		for (int32 Index = 0; Index < Children->Num(); ++Index)
		{
			const FString Found = FirstTextUnder(
				Children->GetChildAt(Index), Depth + 1);
			if (!Found.IsEmpty())
			{
				return Found;
			}
		}
		return FString();
	}
}

FString ULBSpacecraftDevToolset::ProbePieWidgetAt(float X, float Y)
{
	using namespace LBSpacecraftDevToolsetPrivate;
	TSharedPtr<SViewport> Widget = FindPieViewportWidget();
	if (!Widget.IsValid())
	{
		return NoViewportJson();
	}
	const TSharedRef<SViewport> Ref = Widget.ToSharedRef();
	const FVector2D Abs = ToAbsolute(Ref, X, Y);
	const FWidgetPath Path = PathUnder(Ref, Abs);
	const TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetBoolField(TEXT("success"), true);
	Root->SetNumberField(TEXT("absoluteX"), Abs.X);
	Root->SetNumberField(TEXT("absoluteY"), Abs.Y);
	TArray<TSharedPtr<FJsonValue>> Entries;
	FString ButtonLabel;
	for (int32 Index = Path.Widgets.Num() - 1; Index >= 0; --Index)
	{
		const FArrangedWidget& Arranged = Path.Widgets[Index];
		const TSharedRef<FJsonObject> Entry = MakeShared<FJsonObject>();
		Entry->SetStringField(TEXT("type"),
			Arranged.Widget->GetTypeAsString());
		const FGeometry& Geo = Arranged.Geometry;
		Entry->SetNumberField(TEXT("top"), Geo.GetAbsolutePosition().Y);
		Entry->SetNumberField(TEXT("bottom"), Geo.GetAbsolutePosition().Y
			+ Geo.GetAbsoluteSize().Y);
		Entry->SetNumberField(TEXT("left"), Geo.GetAbsolutePosition().X);
		if (Arranged.Widget->GetTypeAsString() == TEXT("STextBlock"))
		{
			Entry->SetStringField(TEXT("text"),
				StaticCastSharedRef<STextBlock>(Arranged.Widget)
					->GetText().ToString());
		}
		if (ButtonLabel.IsEmpty()
			&& Arranged.Widget->GetTypeAsString() == TEXT("SButton"))
		{
			ButtonLabel = FirstTextUnder(Arranged.Widget, 0);
		}
		Entries.Add(MakeShared<FJsonValueObject>(Entry));
	}
	Root->SetArrayField(TEXT("pathLeafFirst"), Entries);
	Root->SetStringField(TEXT("buttonLabel"), ButtonLabel);
	// The hovered widget's label, for comparison with the path: these
	// two disagreeing is exactly the fault being chased.
	return WriteJson(Root);
}

FString ULBSpacecraftDevToolset::SimulatePieMouseMove(float X, float Y)
{
	using namespace LBSpacecraftDevToolsetPrivate;
	TSharedPtr<SViewport> Widget = FindPieViewportWidget();
	if (!Widget.IsValid())
	{
		return NoViewportJson();
	}
	const TSharedRef<SViewport> Ref = Widget.ToSharedRef();
	const FVector2D Abs = ToAbsolute(Ref, X, Y);
	FSlateApplication& Slate = FSlateApplication::Get();
	const FPointerEvent Move(0, 0, Abs, Slate.GetCursorPos(), TSet<FKey>(),
		EKeys::Invalid, 0.f, FModifierKeysState());
	Slate.ProcessMouseMoveEvent(Move);
	const TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetBoolField(TEXT("success"), true);
	Root->SetNumberField(TEXT("absoluteX"), Abs.X);
	Root->SetNumberField(TEXT("absoluteY"), Abs.Y);
	return WriteJson(Root);
}

FString ULBSpacecraftDevToolset::SimulatePieClick(float X, float Y,
	const FString& Button)
{
	using namespace LBSpacecraftDevToolsetPrivate;
	TSharedPtr<SViewport> Widget = FindPieViewportWidget();
	if (!Widget.IsValid())
	{
		return NoViewportJson();
	}
	const TSharedRef<SViewport> Ref = Widget.ToSharedRef();
	const FVector2D Abs = ToAbsolute(Ref, X, Y);
	const FKey Key = ButtonKey(Button);
	FSlateApplication& Slate = FSlateApplication::Get();
	FocusViewport(Ref);
	// LEAVE, THEN ENTER. After a click fires, Slate queues a synthesized
	// mouse move at the REAL cursor - a person's mouse elsewhere on the
	// desktop - which un-hovers the button; a later move back to the
	// same synthetic point is treated as no movement, so hover never
	// returns and SButton's release refuses to click (second hub click
	// silently dropped, 2026-09-02). Step off-window first so the move
	// to the target is a genuine enter.
	const FVector2D Away(-4096.f, -4096.f);
	const FPointerEvent Leave(0, 0, Away, Slate.GetCursorPos(),
		TSet<FKey>(), EKeys::Invalid, 0.f, FModifierKeysState());
	Slate.ProcessMouseMoveEvent(Leave);
	const FPointerEvent Move(0, 0, Abs, Away, TSet<FKey>(),
		EKeys::Invalid, 0.f, FModifierKeysState());
	Slate.ProcessMouseMoveEvent(Move);
	const FWidgetPath Path = PathUnder(Ref, Abs);
	const bool bHoveredBeforeDown = Path.IsValid()
		&& Path.Widgets.Last().Widget->IsHovered();
	if (!Path.IsValid())
	{
		return FailJson(TEXT("Nothing under that point in the PIE window."));
	}
	TSet<FKey> Pressed;
	Pressed.Add(Key);
	const FPointerEvent Down(0, 0, Abs, Abs, Pressed, Key, 0.f,
		FModifierKeysState());
	const FReply DownReply = Slate.RoutePointerDownEvent(Path, Down);
	// A button's press reply asks Slate to capture the pointer; the
	// platform layer then calls Win32 SetCapture, which Windows revokes
	// at once for a window that is not in the foreground - and the
	// button's release checks HasMouseCapture before firing OnClicked.
	// Re-assert the Slate-level captor here, OS not involved.
	if (DownReply.GetMouseCaptor().IsValid() && Slate.GetUser(0).IsValid())
	{
		Slate.GetUser(0)->SetCursorCaptor(
			DownReply.GetMouseCaptor().ToSharedRef(), Path);
	}
	const bool bCapturedAfterDown =
		Slate.GetUser(0).IsValid() && Slate.GetUser(0)->HasAnyCapture();
	const FPointerEvent Up(0, 0, Abs, Abs, TSet<FKey>(), Key, 0.f,
		FModifierKeysState());
	const FReply UpReply = Slate.RoutePointerUpEvent(Path, Up);
	// A game viewport captures the pointer on click; a synthetic click
	// must not leave the REAL cursor confined to the PIE window while
	// a person is using the machine.
	Slate.ReleaseAllPointerCapture();
	// Diagnostics: the widget types under the point, leaf first, so a
	// click that lands on the wrong layer explains itself.
	TArray<TSharedPtr<FJsonValue>> PathTypes;
	for (int32 Index = Path.Widgets.Num() - 1; Index >= 0; --Index)
	{
		PathTypes.Add(MakeShared<FJsonValueString>(
			Path.Widgets[Index].Widget->GetTypeAsString()));
	}
	const TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetBoolField(TEXT("success"), true);
	Root->SetStringField(TEXT("button"), Key.ToString());
	Root->SetBoolField(TEXT("downHandled"), DownReply.IsEventHandled());
	Root->SetBoolField(TEXT("upHandled"), UpReply.IsEventHandled());
	Root->SetBoolField(TEXT("capturedAfterDown"), bCapturedAfterDown);
	Root->SetBoolField(TEXT("hoveredBeforeDown"), bHoveredBeforeDown);
	Root->SetArrayField(TEXT("pathLeafFirst"), PathTypes);
	Root->SetNumberField(TEXT("absoluteX"), Abs.X);
	Root->SetNumberField(TEXT("absoluteY"), Abs.Y);
	return WriteJson(Root);
}

FString ULBSpacecraftDevToolset::SimulatePieWheel(float X, float Y,
	float Delta)
{
	using namespace LBSpacecraftDevToolsetPrivate;
	TSharedPtr<SViewport> Widget = FindPieViewportWidget();
	if (!Widget.IsValid())
	{
		return NoViewportJson();
	}
	const TSharedRef<SViewport> Ref = Widget.ToSharedRef();
	const FVector2D Abs = ToAbsolute(Ref, X, Y);
	FSlateApplication& Slate = FSlateApplication::Get();
	const FPointerEvent Move(0, 0, Abs, Slate.GetCursorPos(), TSet<FKey>(),
		EKeys::Invalid, 0.f, FModifierKeysState());
	Slate.ProcessMouseMoveEvent(Move);
	const FPointerEvent Wheel(0, 0, Abs, Abs, TSet<FKey>(),
		EKeys::MouseWheelAxis, Delta, FModifierKeysState());
	const FWidgetPath Path = PathUnder(Ref, Abs);
	if (!Path.IsValid())
	{
		return FailJson(TEXT("Nothing under that point in the PIE window."));
	}
	Slate.RouteMouseWheelOrGestureEvent(Path, Wheel, nullptr);
	const TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetBoolField(TEXT("success"), true);
	Root->SetNumberField(TEXT("delta"), Delta);
	return WriteJson(Root);
}

FString ULBSpacecraftDevToolset::SimulatePieKey(const FString& KeyName,
	float HoldSeconds)
{
	using namespace LBSpacecraftDevToolsetPrivate;
	TSharedPtr<SViewport> Widget = FindPieViewportWidget();
	if (!Widget.IsValid())
	{
		return NoViewportJson();
	}
	const FKey Key(*KeyName);
	if (!Key.IsValid())
	{
		return FailJson(FString::Printf(
			TEXT("Unknown key '%s' - use FKey names (W, M, Escape, "
				"SpaceBar, One, LeftShift...)"), *KeyName));
	}
	FocusViewport(Widget.ToSharedRef());
	const uint32* KeyCodePtr = nullptr;
	const uint32* CharCodePtr = nullptr;
	FInputKeyManager::Get().GetCodesFromKey(Key, KeyCodePtr, CharCodePtr);
	const uint32 KeyCode = KeyCodePtr != nullptr ? *KeyCodePtr : 0;
	const uint32 CharCode = CharCodePtr != nullptr ? *CharCodePtr : 0;
	FSlateApplication& Slate = FSlateApplication::Get();
	const FKeyEvent DownEvent(Key, FModifierKeysState(), 0, false,
		CharCode, KeyCode);
	Slate.ProcessKeyDownEvent(DownEvent);
	auto Release = [Key, CharCode, KeyCode]()
	{
		if (FSlateApplication::IsInitialized())
		{
			const FKeyEvent UpEvent(Key, FModifierKeysState(), 0, false,
				CharCode, KeyCode);
			FSlateApplication::Get().ProcessKeyUpEvent(UpEvent);
		}
	};
	if (HoldSeconds > 0.f && GEditor != nullptr)
	{
		FTimerHandle Handle;
		GEditor->GetTimerManager()->SetTimer(Handle,
			FTimerDelegate::CreateLambda(Release), HoldSeconds, false);
	}
	else
	{
		Release();
	}
	const TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetBoolField(TEXT("success"), true);
	Root->SetStringField(TEXT("key"), Key.ToString());
	Root->SetNumberField(TEXT("holdSeconds"), HoldSeconds);
	return WriteJson(Root);
}

FString ULBSpacecraftDevToolset::StartPieFloating(int32 Width, int32 Height)
{
	using namespace LBSpacecraftDevToolsetPrivate;
	if (GEditor == nullptr)
	{
		return FailJson(TEXT("No editor."));
	}
	if (GEditor->PlayWorld != nullptr)
	{
		return FailJson(TEXT("PIE is already running - stop it first "
			"(EditorAppToolset StopPIE)."));
	}
	ULevelEditorPlaySettings* Settings =
		GetMutableDefault<ULevelEditorPlaySettings>();
	Settings->LastExecutedPlayModeType = PlayMode_InEditorFloating;
	Settings->NewWindowWidth = FMath::Max(Width, 320);
	Settings->NewWindowHeight = FMath::Max(Height, 240);
	Settings->NewWindowPosition = FIntPoint(0, 0);
	Settings->CenterNewWindow = false;
	FRequestPlaySessionParams Params;
	Params.WorldType = EPlaySessionWorldType::PlayInEditor;
	Params.SessionDestination = EPlaySessionDestinationType::InProcess;
	Params.EditorPlaySettings = Settings;
	// No DestinationSlateViewport: the editor falls through to the
	// play-mode setting above and opens the floating window.
	GEditor->RequestPlaySession(Params);
	const TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetBoolField(TEXT("success"), true);
	Root->SetNumberField(TEXT("width"), Settings->NewWindowWidth);
	Root->SetNumberField(TEXT("height"), Settings->NewWindowHeight);
	Root->SetStringField(TEXT("note"),
		TEXT("requested; poll GetPieViewportInfo for the new size"));
	return WriteJson(Root);
}

/** Module: registers the toolset once the registry is up. Mirrors
 *  VibeUE's own deferral - GEditor may not exist yet at module load. */
class FLineBossCarFactoryEditorModule : public IModuleInterface
{
public:
	virtual void StartupModule() override
	{
		if (IsRunningCommandlet())
		{
			// Cooks and commandlets need no MCP surface, and the
			// registry can stall clean exits.
			return;
		}
		if (GEditor != nullptr)
		{
			RegisterToolset();
		}
		else
		{
			FCoreDelegates::OnPostEngineInit.AddRaw(this,
				&FLineBossCarFactoryEditorModule::RegisterToolset);
		}
	}

	virtual void ShutdownModule() override
	{
		FCoreDelegates::OnPostEngineInit.RemoveAll(this);
		if (UToolsetRegistry::IsAvailable())
		{
			UToolsetRegistry::UnregisterToolsetClass(
				ULBSpacecraftDevToolset::StaticClass());
		}
	}

private:
	void RegisterToolset()
	{
		if (UToolsetRegistry::IsAvailable())
		{
			UToolsetRegistry::RegisterToolsetClass(
				ULBSpacecraftDevToolset::StaticClass());
			UE_LOG(LogTemp, Display, TEXT(
				"LINEBOSS MCP: LBSpacecraftDevToolset registered"));
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT(
				"LINEBOSS MCP: ToolsetRegistry unavailable - the dev "
				"toolset is not exposed this session"));
		}
	}
};

IMPLEMENT_MODULE(FLineBossCarFactoryEditorModule, LineBossCarFactoryEditor)
