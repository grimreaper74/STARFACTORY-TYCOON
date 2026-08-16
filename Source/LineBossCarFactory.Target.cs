using UnrealBuildTool;
using System.Collections.Generic;

public class LineBossCarFactoryTarget : TargetRules
{
    public LineBossCarFactoryTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;

        ExtraModuleNames.Add("LineBossCarFactory");
    }
}
