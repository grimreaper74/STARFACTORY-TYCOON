using UnrealBuildTool;
using System.Collections.Generic;

public class LineBossCarFactoryEditorTarget : TargetRules
{
    public LineBossCarFactoryEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("LineBossCarFactory");
        ExtraModuleNames.Add("LineBossCarFactoryEditor");
    }
}
