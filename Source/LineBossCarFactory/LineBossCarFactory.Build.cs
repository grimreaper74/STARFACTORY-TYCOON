using UnrealBuildTool;

public class LineBossCarFactory : ModuleRules
{
    public LineBossCarFactory(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[]
        {
            "Core", "CoreUObject", "Engine", "InputCore", "Json", "NavigationSystem", "Slate", "SlateCore", "UMG"
        });
    }
}
