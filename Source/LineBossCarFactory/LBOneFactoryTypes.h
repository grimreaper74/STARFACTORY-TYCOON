#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "LBPressShopBuildAuthority.h"
#include "LBOneFactoryTypes.generated.h"

class ALBPressShopBuildAuthority;

/** The four player-facing departments in the first unified factory shell. */
UENUM(BlueprintType)
enum class ELBOneFactoryDepartment : uint8
{
    Press,
    Body,
    Paint,
    Assembly
};

/** One shared, map-authored route type. These are datums, never seeded vehicles. */
UENUM(BlueprintType)
enum class ELBOneFactorySharedSpineRole : uint8
{
    Logistics,
    Service
};

/**
 * Declared provenance for an asset entering the OneFactory presentation.
 * Unspecified always fails. ExternalGenerated fails the NativeOnly policy
 * but is ACCEPTED under GeneratedAllowed when it carries a source record -
 * the 2026-08-24 spacecraft-pivot ruling: what an asset must prove is its
 * record, not its birthplace (see SPACECRAFT_PIVOT_AUTHORITY_v001.md).
 */
UENUM(BlueprintType)
enum class ELBOneFactoryAssetProvenance : uint8
{
    Unspecified,
    NativeCode,
    NativeProcedural,
    NativeAuthored,
    VerifiedPreMeshyNative,
    ExternalGenerated
};

/**
 * Fail-closed asset policies. NativeOnly is the car-era shell policy;
 * GeneratedAllowed (spacecraft era) additionally accepts declared
 * ExternalGenerated assets with a recorded source. Append-only for saves.
 */
UENUM(BlueprintType)
enum class ELBOneFactoryProvenancePolicy : uint8
{
    Unspecified,
    NativeOnly,
    GeneratedAllowed
};

/** Stable, world-space department floor allocation; SizeCm is the full 3D extent. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryDepartmentBay
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Line Boss|OneFactory|Layout")
    FName BayId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Line Boss|OneFactory|Layout")
    ELBOneFactoryDepartment Department = ELBOneFactoryDepartment::Press;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Line Boss|OneFactory|Layout")
    FTransform WorldTransform = FTransform::Identity;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Line Boss|OneFactory|Layout")
    FVector SizeCm = FVector::ZeroVector;

    FBox GetWorldBounds() const;
};

/** Stable shared route/service datum; SizeCm is the full protected volume. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactorySharedSpine
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Line Boss|OneFactory|Layout")
    FName SpineId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Line Boss|OneFactory|Layout")
    ELBOneFactorySharedSpineRole Role = ELBOneFactorySharedSpineRole::Logistics;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Line Boss|OneFactory|Layout")
    FTransform WorldTransform = FTransform::Identity;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Line Boss|OneFactory|Layout")
    FVector SizeCm = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Line Boss|OneFactory|Layout",
        meta=(ClampMin="0.0"))
    float MaximumReachCm = 0.0f;

    FBox GetWorldBounds() const;
};

/**
 * Map-local, shell-only contract for Moorcross Works. It is deliberately free of
 * station definitions, production recipes, inventory and WIP.
 */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryLayoutDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Line Boss|OneFactory|Layout")
    FName LayoutId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Line Boss|OneFactory|Layout")
    FString FactoryDisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Line Boss|OneFactory|Layout")
    FTransform FactoryEnvelopeTransform = FTransform::Identity;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Line Boss|OneFactory|Layout")
    FVector FactoryEnvelopeSizeCm = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Line Boss|OneFactory|Layout")
    TArray<FLBOneFactoryDepartmentBay> DepartmentBays;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Line Boss|OneFactory|Layout")
    TArray<FLBOneFactorySharedSpine> SharedSpines;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Line Boss|OneFactory|Provenance")
    ELBOneFactoryProvenancePolicy ProvenancePolicy =
        ELBOneFactoryProvenancePolicy::NativeOnly;

    /** Must remain false until a later, separately reviewed station-build milestone. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Line Boss|OneFactory|Isolation")
    bool bSeedStationsOnBeginPlay = false;

    FBox GetFactoryEnvelopeBounds() const;
};

/** Mutation-free world snapshot shared by BeginPlay and focused automation. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryWorldAudit
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Audit")
    int32 BootstrapCount = 0;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Audit")
    int32 PressBuildAuthorityCount = 0;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Audit")
    int32 MapOwnedProductionActorCount = 0;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Audit")
    int32 MapOwnedWIPActorCount = 0;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Audit")
    int32 ForbiddenLegacyActorCount = 0;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Audit")
    int32 ForbiddenProvenanceActorCount = 0;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Audit")
    bool bBootstrapUnowned = false;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Audit")
    bool bPressBuildAuthorityUnowned = false;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Audit")
    bool bPressBuildAuthorityMapTagged = false;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Audit")
    bool bBootstrapAndAuthorityShareLevel = false;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|OneFactory|Audit")
    bool bProtectedMapPackage = false;
};

/** Stable IDs are functions so no translation unit depends on static initialisation order. */
namespace LBOneFactoryIds
{
    LINEBOSSCARFACTORY_API FName MoorcrossWorksLayout();
    LINEBOSSCARFACTORY_API FName PressBay();
    LINEBOSSCARFACTORY_API FName BodyBay();
    LINEBOSSCARFACTORY_API FName PaintBay();
    LINEBOSSCARFACTORY_API FName AssemblyBay();
    LINEBOSSCARFACTORY_API FName LogisticsSpine();
    LINEBOSSCARFACTORY_API FName ServiceSpine();
}

/** Pure authoring/validation seam for the native-only OneFactory shell. */
UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactoryLayoutLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Layout")
    static FLBOneFactoryLayoutDefinition MakeMoorcrossWorksShellLayout();

    /** Structural validation suitable for editor tooling and negative tests. */
    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Layout")
    static bool ValidateLayout(const FLBOneFactoryLayoutDefinition& Layout,
        FString& OutReason);

    /** Structural validation plus exact stable IDs, transforms and dimensions. */
    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Layout")
    static bool ValidateMoorcrossWorksLayout(const FLBOneFactoryLayoutDefinition& Layout,
        FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Provenance")
    static bool ValidateAssetProvenance(ELBOneFactoryProvenancePolicy Policy,
        ELBOneFactoryAssetProvenance Provenance, const FString& SourceReference,
        FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Isolation")
    static bool IsProtectedMapPackageName(const FString& PackageName);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Isolation")
    static bool IsForbiddenLegacyActorClassName(const FString& ClassName);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Isolation")
    static bool IsMapOwnedProductionActorClassName(const FString& ClassName);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Isolation")
    static bool ValidateWorldAudit(const FLBOneFactoryWorldAudit& Audit,
        FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Layout")
    static bool ValidatePressBuildAuthorityContract(
        const FLBOneFactoryLayoutDefinition& Layout,
        const ALBPressShopBuildAuthority* Authority, FString& OutReason);

    /**
     * Deterministic map-authoring contract. Runtime code only compares against
     * these arrays; it never writes them into the map-owned authority.
     */
    static void BuildExpectedPressAuthorityContract(
        const FLBOneFactoryLayoutDefinition& Layout,
        TArray<FLBPressShopBuildBay>& OutBuildBays,
        TArray<FLBPressShopProtectedArea>& OutProtectedAreas,
        TArray<FLBPressShopUtilitySpine>& OutUtilitySpines,
        TArray<FLBPressShopLogisticsSpine>& OutLogisticsSpines);
};
