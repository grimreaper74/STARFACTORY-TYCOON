#include "LBSpacecraftInputMap.h"

#include "GameFramework/InputSettings.h"

#define LOCTEXT_NAMESPACE "LBSpacecraftInput"

namespace LBSpacecraftInputMapPrivate
{
	// Unity-build safety: helpers qualified by subject.

	FLBSpacecraftInputRow SpacecraftActionRow(const TCHAR* RowId,
		const TCHAR* MappingName, ELBSpacecraftInputCategory Category,
		const FKey& DefaultKey, const FText& DisplayName,
		bool bRebindable = true, bool bDefaultShift = false,
		const FKey& Extra1 = EKeys::Invalid,
		const FKey& Extra2 = EKeys::Invalid)
	{
		FLBSpacecraftInputRow Row;
		Row.RowId = FName(RowId);
		Row.MappingName = FName(MappingName);
		Row.Kind = ELBSpacecraftInputRowKind::Action;
		Row.Category = Category;
		Row.DefaultKey = DefaultKey;
		Row.bDefaultShift = bDefaultShift;
		Row.ExtraDefaultKey1 = Extra1;
		Row.ExtraDefaultKey2 = Extra2;
		Row.DisplayName = DisplayName;
		Row.bRebindable = bRebindable;
		return Row;
	}

	FLBSpacecraftInputRow SpacecraftAxisRow(const TCHAR* RowId,
		const TCHAR* MappingName, ELBSpacecraftInputCategory Category,
		float AxisScale, const FKey& DefaultKey, const FText& DisplayName,
		bool bRebindable = true)
	{
		FLBSpacecraftInputRow Row;
		Row.RowId = FName(RowId);
		Row.MappingName = FName(MappingName);
		Row.Kind = ELBSpacecraftInputRowKind::AxisKey;
		Row.Category = Category;
		Row.AxisScale = AxisScale;
		Row.DefaultKey = DefaultKey;
		Row.DisplayName = DisplayName;
		Row.bRebindable = bRebindable;
		return Row;
	}

	bool SpacecraftAxisRowMatchesMapping(const FLBSpacecraftInputRow& Row,
		const FInputAxisKeyMapping& Mapping)
	{
		return Mapping.AxisName == Row.MappingName
			&& !Mapping.Key.IsGamepadKey()
			&& FMath::Sign(Mapping.Scale) == FMath::Sign(Row.AxisScale);
	}
}

const TArray<FLBSpacecraftInputRow>& FLBSpacecraftInputMap::GetRows()
{
	using namespace LBSpacecraftInputMapPrivate;
	static const TArray<FLBSpacecraftInputRow> Rows = {
		// CAMERA - WASD pan, Q/E rotation and C/V zoom are the Car
		// Manufacture camera map verbatim (their R/F pitch axis has no
		// home here: the 2.5D framing contract fixes pitch at -35).
		SpacecraftAxisRow(TEXT("PanForward"), TEXT("LB_SC_PanForward"),
			ELBSpacecraftInputCategory::Camera, 1.f, EKeys::W,
			LOCTEXT("PanForward", "PAN FORWARD")),
		SpacecraftAxisRow(TEXT("PanBack"), TEXT("LB_SC_PanForward"),
			ELBSpacecraftInputCategory::Camera, -1.f, EKeys::S,
			LOCTEXT("PanBack", "PAN BACK")),
		SpacecraftAxisRow(TEXT("PanRight"), TEXT("LB_SC_PanRight"),
			ELBSpacecraftInputCategory::Camera, 1.f, EKeys::D,
			LOCTEXT("PanRight", "PAN RIGHT")),
		SpacecraftAxisRow(TEXT("PanLeft"), TEXT("LB_SC_PanRight"),
			ELBSpacecraftInputCategory::Camera, -1.f, EKeys::A,
			LOCTEXT("PanLeft", "PAN LEFT")),
		SpacecraftAxisRow(TEXT("RotateRight"), TEXT("LB_SC_Rotate"),
			ELBSpacecraftInputCategory::Camera, 1.f, EKeys::E,
			LOCTEXT("RotateRight", "ROTATE CAMERA RIGHT")),
		SpacecraftAxisRow(TEXT("RotateLeft"), TEXT("LB_SC_Rotate"),
			ELBSpacecraftInputCategory::Camera, -1.f, EKeys::Q,
			LOCTEXT("RotateLeft", "ROTATE CAMERA LEFT")),
		SpacecraftAxisRow(TEXT("ZoomWheel"), TEXT("LB_SC_ZoomWheel"),
			ELBSpacecraftInputCategory::Camera, 1.f, EKeys::MouseWheelAxis,
			LOCTEXT("ZoomWheel", "ZOOM (WHEEL)"), false),
		SpacecraftAxisRow(TEXT("ZoomIn"), TEXT("LB_SC_ZoomKeys"),
			ELBSpacecraftInputCategory::Camera, 1.f, EKeys::V,
			LOCTEXT("ZoomIn", "ZOOM IN")),
		SpacecraftAxisRow(TEXT("ZoomOut"), TEXT("LB_SC_ZoomKeys"),
			ELBSpacecraftInputCategory::Camera, -1.f, EKeys::C,
			LOCTEXT("ZoomOut", "ZOOM OUT")),
		SpacecraftActionRow(TEXT("DragPan"), TEXT("LB_SC_DragPan"),
			ELBSpacecraftInputCategory::Camera, EKeys::MiddleMouseButton,
			LOCTEXT("DragPan", "DRAG TO PAN")),
		SpacecraftActionRow(TEXT("SiteMap"), TEXT("LB_SC_SiteMap"),
			ELBSpacecraftInputCategory::Camera, EKeys::M,
			LOCTEXT("SiteMap", "SITE MAP")),
		SpacecraftActionRow(TEXT("CameraReset"), TEXT("LB_SC_CameraReset"),
			ELBSpacecraftInputCategory::Camera, EKeys::Home,
			LOCTEXT("CameraReset", "RESET CAMERA")),

		// BUILD - LMB confirms (locked), RMB cancels/deselects, the
		// ghost rotates on the CM Z/X pair with R and F kept alongside.
		SpacecraftActionRow(TEXT("Confirm"), TEXT("LB_SC_PrimaryClick"),
			ELBSpacecraftInputCategory::Build, EKeys::LeftMouseButton,
			LOCTEXT("Confirm", "SELECT / PLACE"), false),
		SpacecraftActionRow(TEXT("Cancel"), TEXT("LB_SC_SecondaryClick"),
			ELBSpacecraftInputCategory::Build, EKeys::RightMouseButton,
			LOCTEXT("Cancel", "CANCEL / DESELECT")),
		SpacecraftActionRow(TEXT("RotateGhost"), TEXT("LB_SC_RotateGhost"),
			ELBSpacecraftInputCategory::Build, EKeys::X,
			LOCTEXT("RotateGhost", "ROTATE GHOST"),
			true, false, EKeys::R, EKeys::F),
		SpacecraftActionRow(TEXT("RotateGhostBack"),
			TEXT("LB_SC_RotateGhostBack"),
			ELBSpacecraftInputCategory::Build, EKeys::Z,
			LOCTEXT("RotateGhostBack", "ROTATE GHOST BACK")),

		// GAME - the CM time row (1 pause, 2/3/4 speeds), Tab section
		// cycling (their backquote is our console key, so the reverse
		// direction rides Shift+Tab), F5/F9 quick save and load.
		SpacecraftActionRow(TEXT("PauseSim"), TEXT("LB_SC_SpeedPause"),
			ELBSpacecraftInputCategory::Game, EKeys::One,
			LOCTEXT("PauseSim", "PAUSE FACTORY")),
		SpacecraftActionRow(TEXT("SpeedNormal"), TEXT("LB_SC_SpeedNormal"),
			ELBSpacecraftInputCategory::Game, EKeys::Two,
			LOCTEXT("SpeedNormal", "NORMAL SPEED")),
		SpacecraftActionRow(TEXT("SpeedFast"), TEXT("LB_SC_SpeedFast"),
			ELBSpacecraftInputCategory::Game, EKeys::Three,
			LOCTEXT("SpeedFast", "FAST SPEED")),
		SpacecraftActionRow(TEXT("SpeedFastest"), TEXT("LB_SC_SpeedFastest"),
			ELBSpacecraftInputCategory::Game, EKeys::Four,
			LOCTEXT("SpeedFastest", "FASTEST SPEED")),
		SpacecraftActionRow(TEXT("PanelNext"), TEXT("LB_SC_PanelNext"),
			ELBSpacecraftInputCategory::Game, EKeys::Tab,
			LOCTEXT("PanelNext", "NEXT PANEL TAB")),
		SpacecraftActionRow(TEXT("PanelPrev"), TEXT("LB_SC_PanelPrev"),
			ELBSpacecraftInputCategory::Game, EKeys::Tab,
			LOCTEXT("PanelPrev", "PREVIOUS PANEL TAB"),
			true, /*bDefaultShift=*/true),
		SpacecraftActionRow(TEXT("QuickSave"), TEXT("LB_SC_QuickSave"),
			ELBSpacecraftInputCategory::Game, EKeys::F5,
			LOCTEXT("QuickSave", "QUICK SAVE")),
		SpacecraftActionRow(TEXT("QuickLoad"), TEXT("LB_SC_QuickLoad"),
			ELBSpacecraftInputCategory::Game, EKeys::F9,
			LOCTEXT("QuickLoad", "QUICK LOAD")),
		SpacecraftActionRow(TEXT("Menu"), TEXT("LB_SC_Menu"),
			ELBSpacecraftInputCategory::Game, EKeys::Escape,
			LOCTEXT("Menu", "MENU / CANCEL"), false),
	};
	return Rows;
}

const FLBSpacecraftInputRow* FLBSpacecraftInputMap::FindRow(FName RowId)
{
	for (const FLBSpacecraftInputRow& Row : GetRows())
	{
		if (Row.RowId == RowId)
		{
			return &Row;
		}
	}
	return nullptr;
}

int32 FLBSpacecraftInputMap::EnsureSpacecraftBindings(UInputSettings& Settings)
{
	using namespace LBSpacecraftInputMapPrivate;
	int32 Added = 0;
	for (const FLBSpacecraftInputRow& Row : GetRows())
	{
		if (Row.Kind == ELBSpacecraftInputRowKind::Action)
		{
			TArray<FInputActionKeyMapping> Existing;
			Settings.GetActionMappingByName(Row.MappingName, Existing);
			bool bHasDesktopKey = false;
			for (const FInputActionKeyMapping& Mapping : Existing)
			{
				if (!Mapping.Key.IsGamepadKey())
				{
					bHasDesktopKey = true;
					break;
				}
			}
			if (bHasDesktopKey)
			{
				continue;
			}
			FInputActionKeyMapping Mapping(Row.MappingName, Row.DefaultKey,
				Row.bDefaultShift);
			Settings.AddActionMapping(Mapping, false);
			++Added;
			for (const FKey& Extra :
				{ Row.ExtraDefaultKey1, Row.ExtraDefaultKey2 })
			{
				if (Extra.IsValid())
				{
					Settings.AddActionMapping(
						FInputActionKeyMapping(Row.MappingName, Extra),
						false);
					++Added;
				}
			}
		}
		else
		{
			TArray<FInputAxisKeyMapping> Existing;
			Settings.GetAxisMappingByName(Row.MappingName, Existing);
			bool bHasRowKey = false;
			for (const FInputAxisKeyMapping& Mapping : Existing)
			{
				if (SpacecraftAxisRowMatchesMapping(Row, Mapping))
				{
					bHasRowKey = true;
					break;
				}
			}
			if (!bHasRowKey)
			{
				Settings.AddAxisMapping(FInputAxisKeyMapping(
					Row.MappingName, Row.DefaultKey, Row.AxisScale), false);
				++Added;
			}
		}
	}
	if (Added > 0)
	{
		Settings.ForceRebuildKeymaps();
	}
	return Added;
}

void FLBSpacecraftInputMap::ResetSpacecraftBindings(UInputSettings& Settings)
{
	using namespace LBSpacecraftInputMapPrivate;
	for (const FLBSpacecraftInputRow& Row : GetRows())
	{
		if (Row.Kind == ELBSpacecraftInputRowKind::Action)
		{
			TArray<FInputActionKeyMapping> Existing;
			Settings.GetActionMappingByName(Row.MappingName, Existing);
			for (const FInputActionKeyMapping& Mapping : Existing)
			{
				if (!Mapping.Key.IsGamepadKey())
				{
					Settings.RemoveActionMapping(Mapping, false);
				}
			}
			Settings.AddActionMapping(FInputActionKeyMapping(
				Row.MappingName, Row.DefaultKey, Row.bDefaultShift), false);
			for (const FKey& Extra :
				{ Row.ExtraDefaultKey1, Row.ExtraDefaultKey2 })
			{
				if (Extra.IsValid())
				{
					Settings.AddActionMapping(
						FInputActionKeyMapping(Row.MappingName, Extra),
						false);
				}
			}
		}
		else
		{
			TArray<FInputAxisKeyMapping> Existing;
			Settings.GetAxisMappingByName(Row.MappingName, Existing);
			for (const FInputAxisKeyMapping& Mapping : Existing)
			{
				if (SpacecraftAxisRowMatchesMapping(Row, Mapping))
				{
					Settings.RemoveAxisMapping(Mapping, false);
				}
			}
			Settings.AddAxisMapping(FInputAxisKeyMapping(
				Row.MappingName, Row.DefaultKey, Row.AxisScale), false);
		}
	}
	Settings.ForceRebuildKeymaps();
}

TArray<FKey> FLBSpacecraftInputMap::GetAllKeys(const UInputSettings& Settings,
	const FLBSpacecraftInputRow& Row)
{
	using namespace LBSpacecraftInputMapPrivate;
	TArray<FKey> Keys;
	if (Row.Kind == ELBSpacecraftInputRowKind::Action)
	{
		TArray<FInputActionKeyMapping> Existing;
		Settings.GetActionMappingByName(Row.MappingName, Existing);
		for (const FInputActionKeyMapping& Mapping : Existing)
		{
			if (!Mapping.Key.IsGamepadKey())
			{
				Keys.AddUnique(Mapping.Key);
			}
		}
	}
	else
	{
		TArray<FInputAxisKeyMapping> Existing;
		Settings.GetAxisMappingByName(Row.MappingName, Existing);
		for (const FInputAxisKeyMapping& Mapping : Existing)
		{
			if (SpacecraftAxisRowMatchesMapping(Row, Mapping))
			{
				Keys.AddUnique(Mapping.Key);
			}
		}
	}
	return Keys;
}

FKey FLBSpacecraftInputMap::GetPrimaryKey(const UInputSettings& Settings,
	const FLBSpacecraftInputRow& Row, bool& bOutShift)
{
	using namespace LBSpacecraftInputMapPrivate;
	bOutShift = false;
	// The engine returns mappings in REVERSE add order, so "first" is an
	// implementation detail: the row's shipped default counts as primary
	// whenever it is still bound (X wins over its R/F extras).
	const TArray<FKey> Keys = GetAllKeys(Settings, Row);
	FKey Primary = EKeys::Invalid;
	if (Keys.Contains(Row.DefaultKey))
	{
		Primary = Row.DefaultKey;
	}
	else if (Keys.Num() > 0)
	{
		Primary = Keys[0];
	}
	if (Primary.IsValid()
		&& Row.Kind == ELBSpacecraftInputRowKind::Action)
	{
		TArray<FInputActionKeyMapping> Existing;
		Settings.GetActionMappingByName(Row.MappingName, Existing);
		for (const FInputActionKeyMapping& Mapping : Existing)
		{
			if (Mapping.Key == Primary)
			{
				bOutShift = Mapping.bShift;
				break;
			}
		}
	}
	return Primary;
}

bool FLBSpacecraftInputMap::IsBindableKey(const FKey& Key)
{
	return Key.IsValid() && !Key.IsGamepadKey() && !Key.IsTouch()
		&& !Key.IsGesture() && Key != EKeys::Escape
		&& Key != EKeys::LeftMouseButton && Key != EKeys::MouseWheelAxis
		&& Key != EKeys::AnyKey;
}

bool FLBSpacecraftInputMap::RebindRow(UInputSettings& Settings, FName RowId,
	const FKey& NewKey, FString& OutReason)
{
	using namespace LBSpacecraftInputMapPrivate;
	const FLBSpacecraftInputRow* Row = FindRow(RowId);
	if (Row == nullptr)
	{
		OutReason = FString::Printf(TEXT("UNKNOWN BINDING %s"),
			*RowId.ToString());
		return false;
	}
	if (!Row->bRebindable)
	{
		OutReason = FString::Printf(TEXT("%s IS FIXED AND CANNOT REBIND"),
			*Row->RowId.ToString());
		return false;
	}
	if (!IsBindableKey(NewKey))
	{
		OutReason = FString::Printf(TEXT("%s CANNOT SERVE AS A BINDING"),
			*NewKey.GetDisplayName().ToString());
		return false;
	}
	for (const FLBSpacecraftInputRow& Other : GetRows())
	{
		if (Other.RowId == Row->RowId)
		{
			continue;
		}
		bool bOtherShift = false;
		if (GetAllKeys(Settings, Other).Contains(NewKey)
			&& !(GetPrimaryKey(Settings, Other, bOtherShift) == NewKey
				&& bOtherShift))
		{
			OutReason = FString::Printf(TEXT("%s IS ALREADY USED BY %s"),
				*NewKey.GetDisplayName().ToString(),
				*Other.RowId.ToString());
			return false;
		}
	}
	if (Row->Kind == ELBSpacecraftInputRowKind::Action)
	{
		TArray<FInputActionKeyMapping> Existing;
		Settings.GetActionMappingByName(Row->MappingName, Existing);
		for (const FInputActionKeyMapping& Mapping : Existing)
		{
			if (!Mapping.Key.IsGamepadKey())
			{
				Settings.RemoveActionMapping(Mapping, false);
			}
		}
		Settings.AddActionMapping(
			FInputActionKeyMapping(Row->MappingName, NewKey), false);
	}
	else
	{
		TArray<FInputAxisKeyMapping> Existing;
		Settings.GetAxisMappingByName(Row->MappingName, Existing);
		for (const FInputAxisKeyMapping& Mapping : Existing)
		{
			if (SpacecraftAxisRowMatchesMapping(*Row, Mapping))
			{
				Settings.RemoveAxisMapping(Mapping, false);
			}
		}
		Settings.AddAxisMapping(FInputAxisKeyMapping(
			Row->MappingName, NewKey, Row->AxisScale), false);
	}
	Settings.ForceRebuildKeymaps();
	OutReason = FString::Printf(TEXT("%s NOW ON %s"),
		*Row->RowId.ToString(), *NewKey.GetDisplayName().ToString());
	return true;
}

#undef LOCTEXT_NAMESPACE
