using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
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
        private const string VirtualEnvironmentFolder = ".venv";
        private const string RequirementsFingerprintFile = ".pneumostabsim_requirements.hash";

        private static readonly string[] RequirementFiles = new[]
        {
            "requirements.txt",
            "requirements-dev.txt",
            "current_requirements.txt",
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
                var pythonPath = EnsureVirtualEnvironment(result);
                if (string.IsNullOrWhiteSpace(pythonPath))
                {
                    return result;
                }

                result.SetPythonExecutable(pythonPath);

                if (!EnsurePythonDependencies(pythonPath!, result))
                {
                    return result;
                }

                if (!VerifyPythonDependencies(pythonPath!, result))
                {
                    return result;
                }

                if (!SynchroniseEnvironmentVariables(pythonPath!, result))
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

        private string? EnsureVirtualEnvironment(EnvironmentPreparationResult result)
        {
            var venvRoot = Path.Combine(_projectRoot, VirtualEnvironmentFolder);
            var scriptsFolder = "Scripts";
            var pythonExecutable = "python.exe";
            var pythonPath = Path.Combine(venvRoot, scriptsFolder, pythonExecutable);

            try
            {
                if (!File.Exists(pythonPath))
                {
                    Directory.CreateDirectory(venvRoot);

                    var systemPython = LocateSystemPython();
                    if (string.IsNullOrWhiteSpace(systemPython))
                    {
                        const string message = "Не удалось найти установленный Python 3.11–3.13 для подготовки виртуального окружения.";
                        result.AddError(message);
                        _logger.LogError(message);
                        return null;
                    }

                    _logger.LogInformation("Creating virtual environment in {VenvRoot} using interpreter {Python}", venvRoot, systemPython);
                    var process = RunProcess(systemPython!, new[] { "-m", "venv", venvRoot }, _projectRoot, timeout: TimeSpan.FromMinutes(5));
                    if (!process.IsSuccess)
                    {
                        var message = $"Failed to create virtual environment (exit code {process.ExitCode}). {process.Error}".Trim();
                        result.AddError(message);
                        _logger.LogError("Failed to create virtual environment. Output: {Output}. Error: {Error}", process.Output, process.Error);
                        return null;
                    }
                }
                else
                {
                    _logger.LogInformation("Using existing virtual environment at {PythonPath}", pythonPath);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to prepare the virtual environment.");
                result.AddError($"Failed to prepare the virtual environment: {ex.Message}");
                return null;
            }

            return pythonPath;
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

        private bool EnsurePythonDependencies(string pythonPath, EnvironmentPreparationResult result)
        {
            try
            {
                var fingerprint = ComputeRequirementsFingerprint();
                var sentinelPath = Path.Combine(_projectRoot, VirtualEnvironmentFolder, RequirementsFingerprintFile);
                var existingFingerprint = File.Exists(sentinelPath) ? File.ReadAllText(sentinelPath).Trim() : string.Empty;

                if (string.Equals(existingFingerprint, fingerprint, StringComparison.Ordinal))
                {
                    _logger.LogInformation("Python dependencies are up to date – skipping installation.");
                    return true;
                }

                _logger.LogInformation("Installing Python dependencies for Visual Studio Insiders profile...");

                var upgradeResult = RunProcess(pythonPath, new[] { "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel" }, _projectRoot, timeout: TimeSpan.FromMinutes(3));
                if (!upgradeResult.IsSuccess)
                {
                    var message = $"Failed to upgrade pip/setuptools (exit code {upgradeResult.ExitCode}). {upgradeResult.Error}".Trim();
                    result.AddError(message);
                    _logger.LogError("pip upgrade failed. Output: {Output}. Error: {Error}", upgradeResult.Output, upgradeResult.Error);
                    return false;
                }

                foreach (var requirements in RequirementFiles)
                {
                    var requirementsPath = Path.Combine(_projectRoot, requirements);
                    if (!File.Exists(requirementsPath))
                    {
                        continue;
                    }

                    var installResult = RunProcess(pythonPath, new[] { "-m", "pip", "install", "-r", requirements }, _projectRoot, timeout: TimeSpan.FromMinutes(5));
                    if (!installResult.IsSuccess)
                    {
                        var message = $"Failed to install dependencies from {requirements} (exit code {installResult.ExitCode}). {installResult.Error}".Trim();
                        result.AddError(message);
                        _logger.LogError("pip install failed for {Requirements}. Output: {Output}. Error: {Error}", requirements, installResult.Output, installResult.Error);
                        return false;
                    }
                }

                Directory.CreateDirectory(Path.GetDirectoryName(sentinelPath)!);
                File.WriteAllText(sentinelPath, fingerprint, Encoding.UTF8);
                _logger.LogInformation("Dependency installation finished successfully.");
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to install Python dependencies.");
                result.AddError($"Failed to install Python dependencies: {ex.Message}");
                return false;
            }
        }

        private bool VerifyPythonDependencies(string pythonPath, EnvironmentPreparationResult result)
        {
            const string verificationScript = "import importlib.util, json, os;"
                + "modules = ['PySide6','numpy','scipy','structlog'];"
                + "missing = [name for name in modules if importlib.util.find_spec(name) is None];"
                + "payload = {'missing': missing, 'warnings': []};"
                + "print(json.dumps(payload))";

            var verificationResult = RunProcess(pythonPath, new[] { "-c", verificationScript }, _projectRoot, timeout: TimeSpan.FromSeconds(30));
            if (!verificationResult.IsSuccess)
            {
                var message = $"Failed to verify Python dependencies (exit code {verificationResult.ExitCode}). {verificationResult.Error}".Trim();
                result.AddError(message);
                _logger.LogError("Dependency verification failed. Output: {Output}. Error: {Error}", verificationResult.Output, verificationResult.Error);
                return false;
            }

            try
            {
                using var document = JsonDocument.Parse(verificationResult.Output);
                if (document.RootElement.TryGetProperty("missing", out var missingElement))
                {
                    var missing = missingElement.EnumerateArray()
                        .Select(x => x.GetString())
                        .Where(x => !string.IsNullOrWhiteSpace(x))
                        .ToList();

                    if (missing.Count > 0)
                    {
                        var message = $"Missing Python modules: {string.Join(", ", missing)}";
                        result.AddError(message);
                        _logger.LogError(message);
                        return false;
                    }
                }
            }
            catch (JsonException ex)
            {
                _logger.LogWarning(ex, "Failed to parse dependency verification response.");
                result.AddWarning($"Failed to parse dependency verification response: {ex.Message}");
            }

            _logger.LogInformation("Python dependencies validated successfully.");
            return true;
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

        private string ComputeRequirementsFingerprint()
        {
            var builder = new StringBuilder();
            foreach (var requirements in RequirementFiles)
            {
                var requirementsPath = Path.Combine(_projectRoot, requirements);
                if (!File.Exists(requirementsPath))
                {
                    continue;
                }

                builder.AppendLine(requirements);
                builder.AppendLine(File.ReadAllText(requirementsPath));
            }

            var data = Encoding.UTF8.GetBytes(builder.ToString());
            var hash = SHA256.HashData(data);
            return Convert.ToHexString(hash);
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
    }
}
