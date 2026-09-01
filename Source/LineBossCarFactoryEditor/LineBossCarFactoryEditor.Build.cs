using System.IO;
using UnrealBuildTool;

// Editor-only module carrying the project's own MCP toolset (owner,
// 2026-09-01: "make your own mcp commands for the bridge to help
// development"). Lives beside the runtime module rather than inside
// the VibeUE clone so the tools are git-tracked project source and
// VibeUE stays an unmodified upstream checkout.
public class LineBossCarFactoryEditor : ModuleRules
{
    public LineBossCarFactoryEditor(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core",
            "CoreUObject",
            "Engine",
        });

        PrivateDependencyModuleNames.AddRange(new string[]
        {
            "Json",
            "UnrealEd",
            "ToolsetRegistry",
            "LineBossCarFactory",
        });

        // The runtime module keeps every header flat in its root (no
        // Public/ split), so a depending module has to name the path.
        PrivateIncludePaths.Add(
            Path.Combine(ModuleDirectory, "..", "LineBossCarFactory"));
    }
}
