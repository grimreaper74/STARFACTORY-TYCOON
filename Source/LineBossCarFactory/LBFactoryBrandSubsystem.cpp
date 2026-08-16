#include "LBFactoryBrandSubsystem.h"

namespace
{
    constexpr float MinimumMachineColourLuminance = 0.035f;
    constexpr float MaximumMachineColourLuminance = 0.78f;
    constexpr float MinimumMachinePairContrast = 1.35f;
}

FString ULBFactoryBrandSubsystem::SanitiseName(const FString& Input)
{
    FString Result;
    Result.Reserve(FMath::Min(Input.Len(), 40));
    bool bPreviousWasSpace = false;
    for (const TCHAR Character : Input)
    {
        if (Result.Len() >= 40) break;
        const bool bWhitespace = FChar::IsWhitespace(Character);
        if (bWhitespace)
        {
            if (!bPreviousWasSpace && !Result.IsEmpty()) Result.AppendChar(TEXT(' '));
            bPreviousWasSpace = true;
            continue;
        }
        if (!FChar::IsPrint(Character)) continue;
        Result.AppendChar(Character);
        bPreviousWasSpace = false;
    }
    Result.TrimStartAndEndInline();
    return Result;
}

bool ULBFactoryBrandSubsystem::IsFiniteUnitColour(const FLinearColor& Colour)
{
    return FMath::IsFinite(Colour.R) && FMath::IsFinite(Colour.G)
        && FMath::IsFinite(Colour.B) && FMath::IsFinite(Colour.A)
        && Colour.R >= 0.0f && Colour.R <= 1.0f
        && Colour.G >= 0.0f && Colour.G <= 1.0f
        && Colour.B >= 0.0f && Colour.B <= 1.0f;
}

float ULBFactoryBrandSubsystem::ContrastRatio(const FLinearColor& A, const FLinearColor& B)
{
    const float Brighter = FMath::Max(A.GetLuminance(), B.GetLuminance());
    const float Darker = FMath::Min(A.GetLuminance(), B.GetLuminance());
    return (Brighter + 0.05f) / (Darker + 0.05f);
}

FLinearColor ULBFactoryBrandSubsystem::GetFixedSafetyYellowColour()
{
    return FLinearColor(1.0f, 0.62f, 0.035f, 1.0f);
}

FLBFactoryMachineLivery ULBFactoryBrandSubsystem::GetMachineLivery() const
{
    FLBFactoryMachineLivery Livery;
    Livery.PrimaryColour = Brand.PrimaryColour;
    Livery.SecondaryColour = Brand.SecondaryColour;
    return Livery;
}

bool ULBFactoryBrandSubsystem::ValidateMachineLiveryColours(
    const FLinearColor Primary, const FLinearColor Secondary, FString& OutReason)
{
    OutReason.Reset();
    if (!IsFiniteUnitColour(Primary) || !IsFiniteUnitColour(Secondary))
    {
        OutReason = TEXT("MACHINE COLOURS MUST BE INSIDE THE STANDARD DISPLAY GAMUT");
        return false;
    }

    const float PrimaryLuminance = Primary.GetLuminance();
    const float SecondaryLuminance = Secondary.GetLuminance();
    if (PrimaryLuminance < MinimumMachineColourLuminance
        || SecondaryLuminance < MinimumMachineColourLuminance)
    {
        OutReason = TEXT("MACHINE COLOURS ARE TOO DARK TO READ ON THE FACTORY FLOOR");
        return false;
    }
    if (PrimaryLuminance > MaximumMachineColourLuminance
        || SecondaryLuminance > MaximumMachineColourLuminance)
    {
        OutReason = TEXT("MACHINE COLOURS ARE TOO BRIGHT TO RETAIN SURFACE DETAIL");
        return false;
    }
    if (ContrastRatio(Primary, Secondary) < MinimumMachinePairContrast)
    {
        OutReason = TEXT("PRIMARY AND FRAME COLOURS NEED MORE CONTRAST");
        return false;
    }
    return true;
}

bool ULBFactoryBrandSubsystem::SetFactoryName(const FString& NewName)
{
    const FString Clean = SanitiseName(NewName);
    if (Clean.IsEmpty()) return false;
    Brand.FactoryName = Clean;
    return true;
}

bool ULBFactoryBrandSubsystem::SetFactoryColours(
    const FLinearColor Primary, const FLinearColor Secondary, const FLinearColor SafetyAccent)
{
    if (!SafetyAccent.Equals(GetFixedSafetyYellowColour(), KINDA_SMALL_NUMBER)) return false;
    return SetMachineLiveryColoursWithoutReason(Primary, Secondary);
}

bool ULBFactoryBrandSubsystem::SetMachineLiveryColours(
    const FLinearColor Primary, const FLinearColor Secondary, FString& OutReason)
{
    if (!ValidateMachineLiveryColours(Primary, Secondary, OutReason)) return false;

    const FLBFactoryMachineLivery PreviousLivery = GetMachineLivery();
    Brand.Version = 2;
    Brand.PrimaryColour = FLinearColor(Primary.R, Primary.G, Primary.B, 1.0f);
    Brand.SecondaryColour = FLinearColor(Secondary.R, Secondary.G, Secondary.B, 1.0f);
    Brand.SafetyAccentColour = GetFixedSafetyYellowColour();
    BroadcastMachineLiveryIfChanged(PreviousLivery);
    return true;
}

bool ULBFactoryBrandSubsystem::SetMachineLiveryColoursWithoutReason(
    const FLinearColor Primary, const FLinearColor Secondary)
{
    FString IgnoredReason;
    return SetMachineLiveryColours(Primary, Secondary, IgnoredReason);
}

bool ULBFactoryBrandSubsystem::CompleteInitialSetup()
{
    FString Reason;
    if (SanitiseName(Brand.FactoryName).IsEmpty()
        || !ValidateMachineLiveryColours(Brand.PrimaryColour, Brand.SecondaryColour, Reason))
        return false;
    Brand.Version = 2;
    Brand.SafetyAccentColour = GetFixedSafetyYellowColour();
    Brand.bInitialSetupComplete = true;
    return true;
}

void ULBFactoryBrandSubsystem::BroadcastMachineLiveryIfChanged(
    const FLBFactoryMachineLivery& PreviousLivery)
{
    const FLBFactoryMachineLivery CurrentLivery = GetMachineLivery();
    if (PreviousLivery.Equals(CurrentLivery)) return;
    ++MachineLiveryRevision;
    MachineLiveryChanged.Broadcast(CurrentLivery);
}

bool ULBFactoryBrandSubsystem::RestoreSaveState(const FLBFactoryBrandSaveState& State)
{
    if ((State.Version != 1 && State.Version != 2)
        || SanitiseName(State.FactoryName).IsEmpty()) return false;

    FLinearColor RestoredPrimary = State.PrimaryColour;
    FLinearColor RestoredSecondary = State.SecondaryColour;
    FString ColourReason;
    if (State.Version == 1)
    {
        // v1 accepted every finite in-gamut pair. Preserve readable legacy choices;
        // repair only formerly legal black/white/indistinguishable combinations so an
        // old campaign is never made unloadable by the new accessibility contract.
        if (!IsFiniteUnitColour(RestoredPrimary) || !IsFiniteUnitColour(RestoredSecondary))
            return false;
        if (!ValidateMachineLiveryColours(RestoredPrimary, RestoredSecondary, ColourReason))
        {
            RestoredPrimary = FLBFactoryMachineLivery().PrimaryColour;
            RestoredSecondary = FLBFactoryMachineLivery().SecondaryColour;
        }
    }
    else if (!ValidateMachineLiveryColours(RestoredPrimary, RestoredSecondary, ColourReason))
    {
        return false;
    }

    // The serialized setup bit remains in v2 so every existing campaign still
    // deserializes. Appearance is now an optional setting, therefore every supported
    // save resumes directly in the factory even if it predates dismissal of onboarding.
    const FLBFactoryMachineLivery PreviousLivery = GetMachineLivery();
    Brand = State;
    Brand.Version = 2;
    Brand.FactoryName = SanitiseName(State.FactoryName);
    Brand.PrimaryColour = RestoredPrimary;
    Brand.SecondaryColour = RestoredSecondary;
    Brand.PrimaryColour.A = Brand.SecondaryColour.A = 1.0f;
    Brand.SafetyAccentColour = GetFixedSafetyYellowColour();
    Brand.bInitialSetupComplete = true;
    BroadcastMachineLiveryIfChanged(PreviousLivery);
    return true;
}
