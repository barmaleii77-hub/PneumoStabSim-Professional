#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Создание файла решения Visual Studio (.sln) для PneumoStabSim-Professional
"""

solution_content = r"""
Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 17
VisualStudioVersion = 17.0.31903.59
MinimumVisualStudioVersion = 10.0.40219.1
Project("{888888A0-9F3D-457C-B088-3A5042F75D52}") = "PneumoStabSim-Professional", "PneumoStabSim-Professional.pyproj", "{6D6D7E5C-8F5A-4B5E-A6F1-2C8E9B3D4A5F}"
EndProject
Global
	GlobalSection(SolutionConfigurationPlatforms) = preSolution
		Debug|Any CPU = Debug|Any CPU
		Release|Any CPU = Release|Any CPU
		Test|Any CPU = Test|Any CPU
	EndGlobalSection
	GlobalSection(ProjectConfigurationPlatforms) = postSolution
		{6D6D7E5C-8F5A-4B5E-A6F1-2C8E9B3D4A5F}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{6D6D7E5C-8F5A-4B5E-A6F1-2C8E9B3D4A5F}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{6D6D7E5C-8F5A-4B5E-A6F1-2C8E9B3D4A5F}.Test|Any CPU.ActiveCfg = Test|Any CPU
	EndGlobalSection
	GlobalSection(SolutionProperties) = preSolution
		HideSolutionNode = FALSE
	EndGlobalSection
	GlobalSection(ExtensibilityGlobals) = postSolution
		SolutionGuid = {1A2B3C4D-5E6F-7890-ABCD-EF1234567890}
	EndGlobalSection
EndGlobal
""".strip()

if __name__ == "__main__":
    with open(
        "PneumoStabSim-Professional.sln", "w", encoding="utf-8", newline="\r\n"
    ) as f:
        f.write(solution_content)
    print("✅ Файл решения PneumoStabSim-Professional.sln успешно создан!")
