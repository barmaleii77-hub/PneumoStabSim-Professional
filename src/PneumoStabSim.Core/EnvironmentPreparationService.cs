using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;

namespace PneumoStabSim.Core
{
    /// <summary>
    /// Ensures the Windows/Visual Studio Insiders runtime environment is ready before the WPF host starts.
    /// Performs virtual environment provisioning, dependency installation, and environment variable synchronisation.
    /// </summary>
    public class EnvironmentPreparationService : IEnvironmentPreparationService
    {
        private static readonly string[] EnsureProjectEnvironmentScriptSegments = new[]
        {
            "tools",
            "visualstudio",
            "ensure_project_environment.py",
        };

        private readonly ILogger<EnvironmentPreparationService> _logger;
        private readonly string _projectRoot;

        public EnvironmentPreparationService(ILogger<EnvironmentPreparationService> logger)
        {
            _logger = logger;
            _projectRoot = LocateProjectRoot();
        }

        /// <inheritdoc />
        public EnvironmentPreparationResult PrepareEnvironment()
        {
            var result = new EnvironmentPreparationResult();

            _logger.LogInformation("Preparing PneumoStabSim Professional environment for Visual Studio Insiders...");

            if (!RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
            {
                const string warning = "Visual Studio Insiders automation is intended for Windows hosts. Skipping Windows-specific provisioning.";
                _logger.LogWarning(warning);
                result.AddWarning(warning);
                return result;
            }

            try
            {
                var ensureStatus = RunEnvironmentProvisioning(result);
                if (ensureStatus is null)
                {
                    return result;
                }

                var pythonPath = ensureStatus.ResolveVirtualEnvironmentPythonPath();
                if (string.IsNullOrWhiteSpace(pythonPath) || !File.Exists(pythonPath))
                {
                    var message = "The Visual Studio Insiders virtual environment does not provide a Python executable.";
                    result.AddError(message);
                    _logger.LogError(message);
                    return result;
                }

                result.SetPythonExecutable(pythonPath);

                ApplyEnvironmentStatusInsights(ensureStatus, result);
                if (!result.Success)
                {
                    return result;
                }

                if (!SynchroniseEnvironmentVariables(pythonPath, result))
                {
                    return result;
                }

                result.MarkEnvironmentSynchronized();
                _logger.LogInformation("Environment preparation completed successfully.");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error while preparing the runtime environment.");
                result.AddError($"Unexpected error while preparing the runtime environment: {ex.Message}");
            }

            return result;
        }

        private string LocateProjectRoot()
        {
            try
            {
                var directory = new DirectoryInfo(AppContext.BaseDirectory);
                while (directory != null)
                {
                    var solutionPath = Path.Combine(directory.FullName, "PneumoStabSim-Professional.sln");
                    if (File.Exists(solutionPath))
                    {
                        return directory.FullName;
                    }

                    directory = directory.Parent;
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Failed to locate solution root, falling back to application base directory.");
            }

            return AppContext.BaseDirectory;
        }

        private EnvironmentStatus? RunEnvironmentProvisioning(EnvironmentPreparationResult result)
        {
            var pythonInterpreter = LocateSystemPython();
            if (string.IsNullOrWhiteSpace(pythonInterpreter))
            {
                const string message = "Не удалось найти установленный Python 3.11–3.13 для подготовки виртуального окружения.";
                result.AddError(message);
                _logger.LogError(message);
                return null;
            }

            var scriptPath = Path.Combine(EnsureProjectEnvironmentScriptSegments.Prepend(_projectRoot).ToArray());
            if (!File.Exists(scriptPath))
            {
                var message = $"Visual Studio environment provisioning script не найден: {scriptPath}";
                _logger.LogError(message);
                result.AddError(message);
                return null;
            }

            var statusPath = Path.Combine(Path.GetTempPath(), $"pneumostabsim_env_status_{Guid.NewGuid():N}.json");

            try
            {
                var arguments = new List<string>
                {
                    scriptPath,
                    "--project-root",
                    _projectRoot,
                    "--status-json",
                    statusPath,
                };

                var environmentOverrides = new Dictionary<string, string>
                {
                    ["PYTHONUTF8"] = "1",
                    ["PYTHONIOENCODING"] = "utf-8",
                    ["PIP_DISABLE_PIP_VERSION_CHECK"] = "1",
                    ["PIP_NO_PYTHON_VERSION_WARNING"] = "1",
                    ["LC_ALL"] = "C.UTF-8",
                    ["LANG"] = "en_US.UTF-8",
                };

                var process = RunProcess(pythonInterpreter!, arguments, _projectRoot, environmentOverrides, timeout: TimeSpan.FromMinutes(8));
                if (!process.IsSuccess)
                {
                    var message = $"Environment provisioning script failed (exit code {process.ExitCode}). {process.Error}".Trim();
                    result.AddError(message);
                    _logger.LogError("Environment provisioning script failed. Output: {Output}. Error: {Error}", process.Output, process.Error);
                    return null;
                }

                LogHelperOutput(process.Output, LogLevel.Information);
                LogHelperOutput(process.Error, LogLevel.Warning);

                if (!File.Exists(statusPath))
                {
                    const string message = "Environment provisioning script did not produce a status report.";
                    result.AddError(message);
                    _logger.LogError(message);
                    return null;
                }

                var statusJson = File.ReadAllText(statusPath);
                var status = EnvironmentStatus.FromJson(statusJson, _logger, result);
                return status;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to execute environment provisioning script.");
                result.AddError($"Failed to execute environment provisioning script: {ex.Message}");
                return null;
            }
            finally
            {
                SafeDeleteFile(statusPath);
            }
        }

        private void ApplyEnvironmentStatusInsights(EnvironmentStatus status, EnvironmentPreparationResult result)
        {
            if (!status.MeetsMinimumRequirement)
            {
                var message = "Обнаруженный интерпретатор Python не соответствует минимальным требованиям (3.11+).";
                result.AddError(message);
                _logger.LogError(message + " Version detected: {Version}", status.InterpreterVersion);
                return;
            }

            if (!status.MeetsRecommendation)
            {
                var warning = "Обнаруженный Python соответствует минимальной версии, но рекомендуется Python 3.13.";
                result.AddWarning(warning);
                _logger.LogWarning(warning + " Version detected: {Version}", status.InterpreterVersion);
            }

            if (!status.DependenciesOk)
            {
                var message = "Некоторые обязательные пакеты Python отсутствуют после автоматической установки.";
                if (status.RemainingMissingDependencies.Any())
                {
                    message += " Missing: " + string.Join(", ", status.RemainingMissingDependencies);
                }

                result.AddError(message);
                _logger.LogError(message);
                return;
            }

            if (status.RequirementsUpdated)
            {
                _logger.LogInformation("Python requirements were refreshed for the Visual Studio Insiders profile.");
            }

            if (status.InstalledMissingDependencies.Any())
            {
                _logger.LogInformation(
                    "Additional Python packages were installed automatically: {Packages}",
                    string.Join(", ", status.InstalledMissingDependencies));
            }

            if (!status.VirtualEnvironmentMatchesExpectation)
            {
                var warning = "Активированное виртуальное окружение не совпадает с ожидаемым .venv. Текущий сеанс Visual Studio может требовать перезапуска.";
                result.AddWarning(warning);
                _logger.LogWarning(warning);
            }

            _logger.LogInformation(
                "Environment provisioning summary: System={System} {Release}, Python={Python} ({Version})",
                status.SystemName,
                status.SystemRelease,
                status.InterpreterPath,
                status.InterpreterVersion);
        }

        private void LogHelperOutput(string? output, LogLevel level)
        {
            if (string.IsNullOrWhiteSpace(output))
            {
                return;
            }

            var lines = output.Split(new[] { Environment.NewLine }, StringSplitOptions.RemoveEmptyEntries);
            foreach (var line in lines)
            {
                _logger.Log(level, "[env-helper] {Line}", line);
            }
        }

        private string? LocateSystemPython()
        {
            var explicitHint = Environment.GetEnvironmentVariable("PNEUMOSTABSIM_PYTHON_HINT");
            if (!string.IsNullOrWhiteSpace(explicitHint) && File.Exists(explicitHint))
            {
                return explicitHint;
            }

            var candidates = new List<string[]>
            {
                new[] { "py", "-3.13" },
                new[] { "py", "-3.12" },
                new[] { "py", "-3.11" },
                new[] { "python3.13" },
                new[] { "python3.12" },
                new[] { "python3.11" },
                new[] { "python3" },
                new[] { "python" },
            };

            foreach (var candidate in candidates)
            {
                var arguments = candidate.Skip(1).ToList();
                arguments.Add("-c");
                arguments.Add("import sys; print(sys.executable)");

                var result = RunProcess(candidate[0], arguments, _projectRoot, timeout: TimeSpan.FromSeconds(20));
                if (!result.IsSuccess)
                {
                    continue;
                }

                var output = result.Output.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries).LastOrDefault();
                if (!string.IsNullOrWhiteSpace(output) && File.Exists(output))
                {
                    _logger.LogInformation("Detected Python interpreter at {InterpreterPath}", output);
                    return output;
                }
            }

            return null;
        }

        private bool SynchroniseEnvironmentVariables(string pythonPath, EnvironmentPreparationResult result)
        {
            var generatorPath = Path.Combine(_projectRoot, "tools", "visualstudio", "generate_insiders_environment.py");
            if (!File.Exists(generatorPath))
            {
                var warning = $"Visual Studio environment generator not found at {generatorPath}.";
                _logger.LogWarning(warning);
                result.AddWarning(warning);
                return true;
            }

            var tempFile = Path.Combine(Path.GetTempPath(), $"pneumostabsim_env_{Guid.NewGuid():N}.json");

            try
            {
                var environmentOverrides = new Dictionary<string, string>
                {
                    ["PYTHONPATH"] = AppendPath(Environment.GetEnvironmentVariable("PYTHONPATH"), _projectRoot),
                };

                var arguments = new List<string>
                {
                    generatorPath,
                    "--project-root",
                    _projectRoot,
                    "--output",
                    tempFile,
                    "--indent",
                    "2",
                };

                var generateResult = RunProcess(pythonPath, arguments, _projectRoot, environmentOverrides, timeout: TimeSpan.FromMinutes(2));
                if (!generateResult.IsSuccess)
                {
                    var message = $"Failed to generate Visual Studio environment (exit code {generateResult.ExitCode}). {generateResult.Error}".Trim();
                    result.AddError(message);
                    _logger.LogError("Environment generation failed. Output: {Output}. Error: {Error}", generateResult.Output, generateResult.Error);
                    return false;
                }

                if (!File.Exists(tempFile))
                {
                    const string message = "Environment generator did not produce an output file.";
                    result.AddError(message);
                    _logger.LogError(message);
                    return false;
                }

                var json = File.ReadAllText(tempFile, Encoding.UTF8);
                var variables = JsonSerializer.Deserialize<Dictionary<string, string>>(json) ?? new Dictionary<string, string>();

                foreach (var variable in variables)
                {
                    Environment.SetEnvironmentVariable(variable.Key, variable.Value, EnvironmentVariableTarget.Process);
                    result.RecordAppliedVariable(variable.Key, variable.Value);
                    _logger.LogInformation("Applied environment variable {Key}={Value}", variable.Key, variable.Value);
                }

                Environment.SetEnvironmentVariable("PNEUMOSTABSIM_PYTHON", pythonPath, EnvironmentVariableTarget.Process);
                result.RecordAppliedVariable("PNEUMOSTABSIM_PYTHON", pythonPath);

                var vsDirectory = Path.Combine(_projectRoot, ".vs");
                Directory.CreateDirectory(vsDirectory);
                var environmentPath = Path.Combine(vsDirectory, "insiders.environment.json");
                File.WriteAllText(environmentPath, json + Environment.NewLine, Encoding.UTF8);
                _logger.LogInformation("Updated Visual Studio Insiders environment file at {Path}", environmentPath);

                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to synchronise Visual Studio environment variables.");
                result.AddError($"Failed to synchronise Visual Studio environment variables: {ex.Message}");
                return false;
            }
            finally
            {
                SafeDeleteFile(tempFile);
            }
        }

        private static string AppendPath(string? existing, string addition)
        {
            if (string.IsNullOrWhiteSpace(addition))
            {
                return existing ?? string.Empty;
            }

            if (string.IsNullOrWhiteSpace(existing))
            {
                return addition;
            }

            return string.Join(Path.PathSeparator, new[] { existing, addition });
        }

        private static void SafeDeleteFile(string? path)
        {
            if (string.IsNullOrWhiteSpace(path))
            {
                return;
            }

            try
            {
                if (File.Exists(path))
                {
                    File.Delete(path);
                }
            }
            catch
            {
                // Ignore cleanup errors.
            }
        }

        private ProcessResult RunProcess(string fileName, IEnumerable<string> arguments, string workingDirectory, IDictionary<string, string>? environment = null, TimeSpan? timeout = null)
        {
            var argumentList = arguments?.ToList() ?? new List<string>();
            var processInfo = new ProcessStartInfo
            {
                FileName = fileName,
                WorkingDirectory = workingDirectory,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                StandardOutputEncoding = Encoding.UTF8,
                StandardErrorEncoding = Encoding.UTF8,
            };

            foreach (var argument in argumentList)
            {
                processInfo.ArgumentList.Add(argument);
            }

            if (environment != null)
            {
                foreach (var entry in environment)
                {
                    processInfo.Environment[entry.Key] = entry.Value;
                }
            }

            _logger.LogDebug("Executing command: {File} {Args}", fileName, string.Join(" ", argumentList));

            try
            {
                using var process = new Process { StartInfo = processInfo };

                var outputBuilder = new StringBuilder();
                var errorBuilder = new StringBuilder();

                process.OutputDataReceived += (_, e) =>
                {
                    if (e.Data != null)
                    {
                        outputBuilder.AppendLine(e.Data);
                    }
                };

                process.ErrorDataReceived += (_, e) =>
                {
                    if (e.Data != null)
                    {
                        errorBuilder.AppendLine(e.Data);
                    }
                };

                if (!process.Start())
                {
                    return ProcessResult.Failed("Process failed to start.");
                }

                process.BeginOutputReadLine();
                process.BeginErrorReadLine();

                var effectiveTimeout = timeout ?? TimeSpan.FromMinutes(2);
                if (!process.WaitForExit((int)effectiveTimeout.TotalMilliseconds))
                {
                    try
                    {
                        process.Kill(entireProcessTree: true);
                    }
                    catch
                    {
                        // Ignore kill errors.
                    }

                    return ProcessResult.TimedOut(outputBuilder.ToString(), errorBuilder.ToString());
                }

                return new ProcessResult(process.ExitCode == 0, process.ExitCode, outputBuilder.ToString(), errorBuilder.ToString(), false);
            }
            catch (Exception ex)
            {
                return ProcessResult.Failed(ex.Message);
            }
        }

        private readonly struct ProcessResult
        {
            public ProcessResult(bool isSuccess, int exitCode, string output, string error, bool timedOut)
            {
                IsSuccess = isSuccess;
                ExitCode = exitCode;
                Output = output;
                Error = error;
                TimedOut = timedOut;
            }

            public bool IsSuccess { get; }
            public int ExitCode { get; }
            public string Output { get; }
            public string Error { get; }
            public bool TimedOut { get; }

            public static ProcessResult TimedOut(string output, string error) => new(false, -1, output, error, true);

            public static ProcessResult Failed(string error) => new(false, -1, string.Empty, error, false);
        }

        private sealed class EnvironmentStatus
        {
            private EnvironmentStatus()
            {
            }

            public string SystemName { get; init; } = string.Empty;
            public string SystemRelease { get; init; } = string.Empty;
            public string InterpreterPath { get; init; } = string.Empty;
            public string InterpreterVersion { get; init; } = string.Empty;
            public bool MeetsRecommendation { get; init; }
            public bool MeetsMinimumRequirement { get; init; }
            public string VirtualEnvironmentPath { get; init; } = string.Empty;
            public bool DependenciesOk { get; init; }
            public IReadOnlyList<string> InstalledMissingDependencies { get; init; } = Array.Empty<string>();
            public IReadOnlyList<string> RemainingMissingDependencies { get; init; } = Array.Empty<string>();
            public bool RequirementsUpdated { get; init; }
            public bool VirtualEnvironmentMatchesExpectation { get; init; }

            public string? ResolveVirtualEnvironmentPythonPath()
            {
                if (string.IsNullOrWhiteSpace(VirtualEnvironmentPath))
                {
                    return null;
                }

                var scriptsFolder = RuntimeInformation.IsOSPlatform(OSPlatform.Windows) ? "Scripts" : "bin";
                var executableName = RuntimeInformation.IsOSPlatform(OSPlatform.Windows) ? "python.exe" : "python";
                // Преобразуем путь к POSIX формату для совместимости с Python/QML
                var combinedPath = Path.Combine(VirtualEnvironmentPath, scriptsFolder, executableName);
                return combinedPath.Replace('\\', '/');
            }

            public static EnvironmentStatus? FromJson(string json, ILogger logger, EnvironmentPreparationResult result)
            {
                try
                {
                    using var document = JsonDocument.Parse(json);
                    var root = document.RootElement;

                    var platform = root.GetProperty("platform");
                    var python = root.GetProperty("python");
                    var virtualEnv = root.GetProperty("virtual_environment");
                    var dependencies = root.GetProperty("dependencies");

                    var installed = ExtractStringList(dependencies, "installed_missing");
                    var remaining = ExtractStringList(dependencies, "remaining_missing");

                    return new EnvironmentStatus
                    {
                        SystemName = platform.GetProperty("system").GetString() ?? string.Empty,
                        SystemRelease = platform.GetProperty("release").GetString() ?? string.Empty,
                        InterpreterPath = python.GetProperty("executable").GetString() ?? string.Empty,
                        InterpreterVersion = python.GetProperty("version").GetString() ?? string.Empty,
                        MeetsRecommendation = python.GetProperty("meets_recommendation").GetBoolean(),
                        MeetsMinimumRequirement = python.GetProperty("meets_minimum").GetBoolean(),
                        VirtualEnvironmentPath = virtualEnv.GetProperty("path").GetString() ?? string.Empty,
                        DependenciesOk = dependencies.GetProperty("ok").GetBoolean(),
                        InstalledMissingDependencies = installed,
                        RemainingMissingDependencies = remaining,
                        RequirementsUpdated = dependencies.GetProperty("requirements_updated").GetBoolean(),
                        VirtualEnvironmentMatchesExpectation = virtualEnv.GetProperty("active_matches_expected").GetBoolean(),
                    };
                }
                catch (JsonException ex)
                {
                    logger.LogError(ex, "Ошибка парсинга JSON при обработке статуса окружения.");
                    result.AddError($"Ошибка парсинга JSON статуса окружения: {ex.Message}");
                    return null;
                }
                catch (InvalidOperationException ex)
                {
                    logger.LogError(ex, "Ошибка доступа к свойствам JSON при обработке статуса окружения.");
                    result.AddError($"Ошибка доступа к свойствам JSON статуса окружения: {ex.Message}");
                    return null;
                }
                catch (ArgumentException ex)
                {
                    logger.LogError(ex, "Ошибка аргументов при обработке статуса окружения.");
                    result.AddError($"Ошибка аргументов статуса окружения: {ex.Message}");
                    return null;
                }
            }

            private static List<string> ExtractStringList(JsonElement container, string property)
            {
                if (!container.TryGetProperty(property, out var element) || element.ValueKind != JsonValueKind.Array)
                {
                    return new List<string>();
                }

                // Используем LINQ для фильтрации и сбора строк из массива JSON
                return element.EnumerateArray()
                    .Select(item => item.GetString())
                    .Where(value => !string.IsNullOrWhiteSpace(value))
                    .ToList();
            }
        }
    }
}
