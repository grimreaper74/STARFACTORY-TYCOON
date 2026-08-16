using UnrealBuildTool;

public class LineBossSupportRobotsRuntimeV002 : ModuleRules
{
    public LineBossSupportRobotsRuntimeV002(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[]
        {
            "Core",
            "CoreUObject",
            "Engine"
        });
    }
}
