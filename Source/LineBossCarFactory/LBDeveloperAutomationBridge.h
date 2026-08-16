#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBFactoryBuildMachine.h"
#include "LBDeveloperAutomationBridge.generated.h"

class FJsonObject;

/**
 * Explicitly enabled, local-only control surface for repeatable development play tests.
 *
 * There is deliberately no socket or web server. A local client atomically places ordered
 * command files in Saved/AutomationBridge/inbox and reads terminal replies from outbox.
 * ALBGameMode never constructs this actor in Shipping builds or without the exact launch flag.
 */
UCLASS(Transient, NotBlueprintable)
class LINEBOSSCARFACTORY_API ALBDeveloperAutomationBridge : public AActor
{
    GENERATED_BODY()

public:
    ALBDeveloperAutomationBridge();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    /** Exact, independently testable launch gate. Similar-looking switches are not accepted. */
    static bool IsEnabledFromCommandLine(const TCHAR* CommandLine);

    /** Stable external name used by replies and state snapshots. */
    static FString SerializeMachineType(ELBFactoryBuildMachineType Type);
    /** Accepts the documented canonical machine name and narrowly scoped compatibility aliases. */
    static bool TryParseMachineType(FString Name, ELBFactoryBuildMachineType& OutType);

    bool IsBridgeEnabled() const { return bBridgeEnabled; }
    const FString& GetBridgeRootDirectory() const { return RootDirectory; }
    const FString& GetInboxDirectory() const { return InboxDirectory; }
    const FString& GetOutboxDirectory() const { return OutboxDirectory; }
    const FString& GetSessionId() const { return SessionId; }
    int64 GetExpectedSequence() const { return ExpectedSequence; }

#if WITH_DEV_AUTOMATION_TESTS
    /** Starts an isolated mailbox beneath Saved/AutomationBridgeTests for transient-world tests. */
    bool StartForTesting(const FString& SafeLeafName);
    int32 PumpForTesting();
#endif

private:
    struct FProcessedCommandRecord
    {
        FString Digest;
        int64 OriginalSequence = 0;
        bool bSucceeded = false;
    };

    bool StartBridge(const FString& TestLeafName = FString());
    void StopBridge();
    int32 ProcessReadyCommands();
    bool ProcessReadyCommand(const FString& Filename, int64 Sequence, const FString& FilenameCommandId);
    bool ExecuteCommand(const FString& Type, const TSharedPtr<FJsonObject>& Args,
        const FString& CommandId, TSharedPtr<FJsonObject>& OutResult,
        FString& OutErrorCode, FString& OutErrorMessage);

    TSharedPtr<FJsonObject> CaptureState() const;
    void WriteSessionDescriptor();
    void WriteStateSnapshot();
    bool WriteJsonAtomic(const FString& FinalPath, const TSharedRef<FJsonObject>& Object) const;
    bool WriteTextAtomic(const FString& FinalPath, const FString& Text) const;
    bool IsPathInsideRoot(const FString& Path) const;

    static bool ParseReadyFilename(const FString& Filename, int64& OutSequence,
        FString& OutCommandId);
    static bool IsSafeToken(const FString& Value, int32 MaximumLength = 64);
    static FString NormalizeKey(FString Value);
    static FString UtcNowString();

    bool bBridgeEnabled = false;
    FString RootDirectory;
    FString SessionDirectory;
    FString InboxDirectory;
    FString ProcessingDirectory;
    FString OutboxDirectory;
    FString ArchiveDirectory;
    FString ScreenshotDirectory;
    FString SessionId;
    int64 ExpectedSequence = 1;
    int64 StateRevision = 0;
    float HeartbeatAccumulator = 0.0f;
    TMap<FString, FProcessedCommandRecord> ProcessedCommands;
};
