#include "LBSpacecraftDevToolset.h"

#include "Dom/JsonObject.h"
#include "Editor.h"
#include "Engine/World.h"
#include "Framework/Application/SlateApplication.h"
#include "GenericPlatform/GenericWindow.h"
#include "Input/Events.h"
#include "Input/HittestGrid.h"
#include "Layout/WidgetPath.h"
#include "InputCoreTypes.h"
#include "Slate/SceneViewport.h"
#include "TimerManager.h"
#include "Widgets/SViewport.h"
#include "Widgets/SWindow.h"
#include "Settings/LevelEditorPlaySettings.h"
#include "LBSpacecraftBuildAuthority.h"
#include "LBSpacecraftGameMode.h"
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
	// Move first so hover state and the game's cached cursor position
	// (what GetHitResultUnderCursor reads) agree with where we press.
	const FPointerEvent Move(0, 0, Abs, Slate.GetCursorPos(), TSet<FKey>(),
		EKeys::Invalid, 0.f, FModifierKeysState());
	Slate.ProcessMouseMoveEvent(Move);
	const FWidgetPath Path = PathUnder(Ref, Abs);
	if (!Path.IsValid())
	{
		return FailJson(TEXT("Nothing under that point in the PIE window."));
	}
	TSet<FKey> Pressed;
	Pressed.Add(Key);
	const FPointerEvent Down(0, 0, Abs, Abs, Pressed, Key, 0.f,
		FModifierKeysState());
	Slate.RoutePointerDownEvent(Path, Down);
	const FPointerEvent Up(0, 0, Abs, Abs, TSet<FKey>(), Key, 0.f,
		FModifierKeysState());
	Slate.RoutePointerUpEvent(Path, Up);
	// A game viewport captures the pointer on click; a synthetic click
	// must not leave the REAL cursor confined to the PIE window while
	// a person is using the machine.
	Slate.ReleaseAllPointerCapture();
	const TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetBoolField(TEXT("success"), true);
	Root->SetStringField(TEXT("button"), Key.ToString());
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
