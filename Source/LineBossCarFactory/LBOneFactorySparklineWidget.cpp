#include "LBOneFactorySparklineWidget.h"

#include "Rendering/DrawElements.h"

int32 SLBOneFactorySparkline::OnPaint(const FPaintArgs& Args,
    const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
    FSlateWindowElementList& OutDrawElements, int32 LayerId,
    const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
    const FVector2D Size = AllottedGeometry.GetLocalSize();
    const float Inset = 2.0f;

    // Faint baseline so an empty or flat graph still reads as a graph.
    TArray<FVector2D> Baseline;
    Baseline.Add(FVector2D(Inset, Size.Y - Inset));
    Baseline.Add(FVector2D(Size.X - Inset, Size.Y - Inset));
    FSlateDrawElement::MakeLines(OutDrawElements, LayerId,
        AllottedGeometry.ToPaintGeometry(), Baseline, ESlateDrawEffect::None,
        FLinearColor(1.0f, 1.0f, 1.0f, 0.15f), true, 1.0f);

    if (Samples.Num() < 2)
    {
        return LayerId + 1;
    }

    float MaxSample = 1.0f;
    for (const float Sample : Samples)
    {
        MaxSample = FMath::Max(MaxSample, Sample);
    }

    TArray<FVector2D> Points;
    Points.Reserve(Samples.Num());
    const float UsableX = Size.X - Inset * 2.0f;
    const float UsableY = Size.Y - Inset * 2.0f;
    for (int32 Index = 0; Index < Samples.Num(); ++Index)
    {
        const float Alpha = Samples.Num() > 1
            ? static_cast<float>(Index) / (Samples.Num() - 1) : 0.0f;
        const float Normal = FMath::Clamp(Samples[Index] / MaxSample,
            0.0f, 1.0f);
        Points.Add(FVector2D(Inset + Alpha * UsableX,
            Inset + (1.0f - Normal) * UsableY));
    }
    FSlateDrawElement::MakeLines(OutDrawElements, LayerId + 1,
        AllottedGeometry.ToPaintGeometry(), Points, ESlateDrawEffect::None,
        LineColor, true, 2.0f);
    return LayerId + 2;
}

void ULBOneFactorySparkline::SetSamples(const TArray<float>& InSamples)
{
    PendingSamples = InSamples;
    if (SlateSparkline.IsValid())
    {
        SlateSparkline->SetSamples(InSamples);
    }
}

void ULBOneFactorySparkline::SetLineColor(const FLinearColor& InColor)
{
    PendingColor = InColor;
    if (SlateSparkline.IsValid())
    {
        SlateSparkline->SetLineColor(InColor);
    }
}

TSharedRef<SWidget> ULBOneFactorySparkline::RebuildWidget()
{
    SlateSparkline = SNew(SLBOneFactorySparkline);
    SlateSparkline->SetSamples(PendingSamples);
    SlateSparkline->SetLineColor(PendingColor);
    return SlateSparkline.ToSharedRef();
}

void ULBOneFactorySparkline::ReleaseSlateResources(bool bReleaseChildren)
{
    Super::ReleaseSlateResources(bReleaseChildren);
    SlateSparkline.Reset();
}
