#pragma once

#include "Components/Widget.h"
#include "CoreMinimal.h"
#include "Widgets/SLeafWidget.h"
#include "LBOneFactorySparklineWidget.generated.h"

/**
 * Slate leaf that paints a normalized polyline over a faint baseline.
 * The detail panel uses it for the trailing production-rate graph;
 * samples arrive oldest-first and scale to their own maximum.
 */
class SLBOneFactorySparkline : public SLeafWidget
{
public:
    SLATE_BEGIN_ARGS(SLBOneFactorySparkline) {}
    SLATE_END_ARGS()

    void Construct(const FArguments& InArgs) {}

    void SetSamples(const TArray<float>& InSamples)
    {
        Samples = InSamples;
    }
    void SetLineColor(const FLinearColor& InColor) { LineColor = InColor; }

    virtual int32 OnPaint(const FPaintArgs& Args,
        const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
        FSlateWindowElementList& OutDrawElements, int32 LayerId,
        const FWidgetStyle& InWidgetStyle,
        bool bParentEnabled) const override;

    virtual FVector2D ComputeDesiredSize(float) const override
    {
        return FVector2D(220.0f, 44.0f);
    }

private:
    TArray<float> Samples;
    FLinearColor LineColor = FLinearColor::White;
};

/** UMG wrapper so the code-built widget tree can place the sparkline. */
UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactorySparkline : public UWidget
{
    GENERATED_BODY()

public:
    void SetSamples(const TArray<float>& InSamples);
    void SetLineColor(const FLinearColor& InColor);

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void ReleaseSlateResources(bool bReleaseChildren) override;

private:
    TSharedPtr<SLBOneFactorySparkline> SlateSparkline;
    TArray<float> PendingSamples;
    FLinearColor PendingColor = FLinearColor::White;
};
