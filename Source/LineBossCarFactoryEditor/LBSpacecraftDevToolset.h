#pragma once

#include "CoreMinimal.h"
#include "ToolsetRegistry/ToolsetDefinition.h"

#include "LBSpacecraftDevToolset.generated.h"

/**
 * The project's own MCP toolset (owner, 2026-09-01: "make your own mcp
 * commands for the bridge to help development"). Registered with the
 * engine's ToolsetRegistry so the editor's loopback MCP server exposes
 * it next to the stock toolsets - reachable through call_tool with the
 * namespaced toolset name (confirm the exact name with list_toolsets).
 *
 * Every function is static and runs on the game thread (the registry
 * marshals). Every function returns a JSON string: {"success": true,
 * ...} or {"success": false, "error": "..."} - never a bare value, so
 * a client can always parse one shape.
 *
 * Why these tools exist: with only the generic surface
 * (execute_python_code, capture_image), every "what is the sim doing"
 * question during the 2026-09-01 overnight session cost a screenshot
 * round-trip or a headless relaunch. These read the authorities
 * directly.
 */
UCLASS(BlueprintType)
class ULBSpacecraftDevToolset : public UToolsetDefinition
{
	GENERATED_BODY()

public:
	/** The whole factory as one JSON document: money, stations and
	 *  their crews, commissioning and route, track, contracts, every
	 *  unit's stage and quality state, power budget, deliveries, and
	 *  the coordinator's last start refusal. Reads the live PIE
	 *  world's authorities; refuses with success=false when no PIE
	 *  session is running. */
	UFUNCTION(BlueprintCallable, meta = (AICallable),
		Category = "LineBoss|Dev")
	static FString GetSpacecraftFactoryStatus();

	/** Runs one console command in the live PIE world (the LB.* dev
	 *  commands especially - BuildLine, Start, Speed, Save, Load,
	 *  Enter, Watch, Screenshot, After). One call, no python quoting.
	 *  Returns {"success", "command", "handled"} - handled=false means
	 *  no command processor claimed it (typo or wrong build). */
	UFUNCTION(BlueprintCallable, meta = (AICallable),
		Category = "LineBoss|Dev")
	static FString RunSpacecraftConsoleCommand(const FString& Command);
};
