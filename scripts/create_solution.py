#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Создание файла решения Visual Studio (.sln) для PneumoStabSim-Professional
"""

solution_content = """
Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 17
VisualStudioVersion = 17.0.31903.59
MinimumVisualStudioVersion = 10.0.40219.1
Project("{888888A0-9F3D-457C-B088-3A5042F75D52}") = "PneumoStabSim-Professional", "PneumoStabSim-Professional.pyproj", "{6D6D7E5C-8F5A-4B5E-A6F1-2C8E9B3D4A5F}"
EndProject
Global
\tGlobalSection(SolutionConfigurationPlatforms) = preSolution
\t\tDebug|Any CPU = Debug|Any CPU
\t\tRelease|Any CPU = Release|Any CPU
\t\tTest|Any CPU = Test|Any CPU
\tEndGlobalSection
\tGlobalSection(ProjectConfigurationPlatforms) = postSolution
\t\t{6D6D7E5C-8F5A-4B5E-A6F1-2C8E9B3D4A5F}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
\t\t{6D6D7E5C-8F5A-4B5E-A6F1-2C8E9B3D4A5F}.Release|Any CPU.ActiveCfg = Release|Any CPU
\t\t{6D6D7E5C-8F5A-4B5E-A6F1-2C8E9B3D4A5F}.Test|Any CPU.ActiveCfg = Test|Any CPU
\tEndGlobalSection
\tGlobalSection(SolutionProperties) = preSolution
\t\tHideSolutionNode = FALSE
\tEndGlobalSection
\tGlobalSection(ExtensibilityGlobals) = postSolution
\t\tSolutionGuid = {1A2B3C4D-5E6F-7890-ABCD-EF1234567890}
\tEndGlobalSection
EndGlobal
""".strip()

if __name__ == "__main__":
    with open(
        "PneumoStabSim-Professional.sln", "w", encoding="utf-8", newline="\r\n"
    ) as f:
        f.write(solution_content)
    print("✅ Файл решения PneumoStabSim-Professional.sln успешно создан!")
