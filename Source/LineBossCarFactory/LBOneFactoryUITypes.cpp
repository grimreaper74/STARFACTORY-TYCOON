#include "LBOneFactoryUITypes.h"

#define LOCTEXT_NAMESPACE "LineBossOneFactoryUI"

namespace LBOneFactoryUIPrivate
{
    FLinearColor FromOkabeIto(const uint8 R, const uint8 G, const uint8 B)
    {
        return FLinearColor::FromSRGBColor(FColor(R, G, B));
    }
}

FLBOneFactoryStatusToken ULBOneFactoryUITokens::TokenForStatus(
    const ELBOneFactoryStationStatus Status)
{
    using namespace LBOneFactoryUIPrivate;
    FLBOneFactoryStatusToken Token;
    Token.Status = Status;
    switch (Status)
    {
    case ELBOneFactoryStationStatus::Working:
        Token.Colour = FromOkabeIto(0, 158, 115);      // bluish green
        Token.Glyph = ELBOneFactoryStatusGlyph::CircleFilled;
        Token.Severity = ELBOneFactoryAlertSeverity::Passive;
        Token.CauseLabel = LOCTEXT("CauseWorking", "Running");
        break;
    case ELBOneFactoryStationStatus::Starved:
        Token.Colour = FromOkabeIto(230, 159, 0);      // orange
        Token.Glyph = ELBOneFactoryStatusGlyph::Triangle;
        Token.Severity = ELBOneFactoryAlertSeverity::Inbox;
        Token.CauseLabel = LOCTEXT("CauseStarved",
            "Starved - no material from {0}");
        break;
    case ELBOneFactoryStationStatus::Blocked:
        Token.Colour = FromOkabeIto(213, 94, 0);       // vermillion
        Token.Glyph = ELBOneFactoryStatusGlyph::Square;
        Token.Severity = ELBOneFactoryAlertSeverity::Toast;
        Token.CauseLabel = LOCTEXT("CauseBlocked",
            "Blocked - {0} cannot accept");
        break;
    case ELBOneFactoryStationStatus::QualityHold:
        Token.Colour = FromOkabeIto(86, 180, 233);     // sky blue
        Token.Glyph = ELBOneFactoryStatusGlyph::Diamond;
        Token.Severity = ELBOneFactoryAlertSeverity::Toast;
        Token.CauseLabel = LOCTEXT("CauseQualityHold",
            "Quality hold - awaiting decision");
        break;
    case ELBOneFactoryStationStatus::WearCritical:
        Token.Colour = FromOkabeIto(240, 228, 66);     // yellow
        Token.Glyph = ELBOneFactoryStatusGlyph::Wrench;
        Token.Severity = ELBOneFactoryAlertSeverity::Inbox;
        Token.CauseLabel = LOCTEXT("CauseWearCritical",
            "Fleet wear critical - service due");
        break;
    case ELBOneFactoryStationStatus::Offline:
        Token.Colour = FromOkabeIto(153, 153, 153);    // grey
        Token.Glyph = ELBOneFactoryStatusGlyph::Cross;
        Token.Severity = ELBOneFactoryAlertSeverity::Toast;
        Token.CauseLabel = LOCTEXT("CauseOffline",
            "Offline - department not commissioned");
        break;
    case ELBOneFactoryStationStatus::Paused:
    default:
        Token.Colour = FromOkabeIto(204, 121, 167);    // reddish purple
        Token.Glyph = ELBOneFactoryStatusGlyph::BarsPaused;
        Token.Severity = ELBOneFactoryAlertSeverity::Passive;
        Token.CauseLabel = LOCTEXT("CausePaused", "Paused by you");
        break;
    }
    return Token;
}

float ULBOneFactoryUITokens::StampsToRatePerHour(const int32 StampCount,
    const float WindowSimSeconds)
{
    if (StampCount <= 0 || WindowSimSeconds <= 0.0f)
    {
        return 0.0f;
    }
    return static_cast<float>(StampCount) * 3600.0f / WindowSimSeconds;
}

#undef LOCTEXT_NAMESPACE
