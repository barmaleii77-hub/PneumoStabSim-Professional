using Microsoft.Extensions.Logging;
using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Diagnostics;
using System.Text.Json;

namespace PneumoStabSim.Core
{
    /// <summary>
    /// Python engine service implementation using process-based integration
    /// More reliable than Python.NET for cross-platform compatibility
    /// </summary>
    public class PythonEngineService : IPythonEngineService, IDisposable
    {
        private readonly ILogger<PythonEngineService> _logger;
        private bool _isInitialized = false;
        private bool _disposed = false;
        private string? _pythonExecutable;

        public bool IsInitialized => _isInitialized;

        public PythonEngineService(ILogger<PythonEngineService> logger)
        {
            _logger = logger;
        }

        public bool Initialize()
        {
            try
            {
                if (_isInitialized)
                    return true;

                _logger.LogInformation("Initializing Python engine...");

                // Find Python executable
                _pythonExecutable = FindPythonExecutable();

                if (string.IsNullOrEmpty(_pythonExecutable))
                {
                    _logger.LogError("Python executable not found");
                    return false;
                }

                // Test Python installation
                var testResult = ExecutePythonCommand("import sys; print(sys.version)");

                if (!testResult.Success)
                {
                    _logger.LogError($"Python test failed: {testResult.Error}");
                    return false;
                }

                _logger.LogInformation($"Python version: {testResult.Output?.Trim()}");

                // Test required modules
                var moduleTestScript = @"
import sys
try:
    import numpy, scipy, PySide6, matplotlib
    print('All required modules available')
except ImportError as e:
    print(f'Missing module: {e}')
    sys.exit(1)
";
                var moduleTest = ExecutePythonCommand(moduleTestScript);

                if (!moduleTest.Success)
                {
                    _logger.LogError($"Required Python modules missing: {moduleTest.Error}");
                    return false;
                }

                _isInitialized = true;
                _logger.LogInformation("Python engine initialized successfully");
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to initialize Python engine");
                return false;
            }
        }

        public void Shutdown()
        {
            try
            {
                if (_isInitialized)
                {
                    _logger.LogInformation("Shutting down Python engine...");
                    _isInitialized = false;
                    _logger.LogInformation("Python engine shut down successfully");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error shutting down Python engine");
            }
        }

        public object? ExecuteScript(string script)
        {
            if (!_isInitialized)
            {
                _logger.LogWarning("Python engine not initialized");
                return null;
            }

            try
            {
                var result = ExecutePythonCommand(script);
                return result.Success ? result.Output : null;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error executing Python script");
                return null;
            }
        }

        public T? CallFunction<T>(string moduleName, string functionName, params object[] args)
        {
            if (!_isInitialized)
            {
                _logger.LogWarning("Python engine not initialized");
                return default;
            }

            try
            {
                // Convert arguments to JSON for Python
                var argsJson = JsonSerializer.Serialize(args);

                var script = $@"
import sys
import json
sys.path.insert(0, '.')
sys.path.insert(0, 'src')

from {moduleName} import {functionName}
args = json.loads(r'{argsJson}')
result = {functionName}(*args) if args else {functionName}()
print(json.dumps(result) if result is not None else 'null')
";

                var result = ExecutePythonCommand(script);

                if (!result.Success || string.IsNullOrEmpty(result.Output))
                {
                    return default;
                }

                if (typeof(T) == typeof(string))
                {
                    return (T)(object)result.Output.Trim();
                }

                try
                {
                    return JsonSerializer.Deserialize<T>(result.Output.Trim());
                }
                catch
                {
                    // If JSON deserialization fails, try direct conversion
                    return (T)Convert.ChangeType(result.Output.Trim(), typeof(T));
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Error calling Python function {moduleName}.{functionName}");
                return default;
            }
        }

        private string? FindPythonExecutable()
        {
            var explicitPython = Environment.GetEnvironmentVariable("PNEUMOSTABSIM_PYTHON");
            if (!string.IsNullOrWhiteSpace(explicitPython) && File.Exists(explicitPython))
            {
                _logger.LogInformation("Using Python interpreter defined by PNEUMOSTABSIM_PYTHON: {Python}", explicitPython);
                return explicitPython;
            }

            var virtualEnv = Environment.GetEnvironmentVariable("VIRTUAL_ENV");
            if (!string.IsNullOrWhiteSpace(virtualEnv))
            {
                var scriptsDirectory = RuntimeInformation.IsOSPlatform(OSPlatform.Windows) ? "Scripts" : "bin";
                var pythonExecutable = RuntimeInformation.IsOSPlatform(OSPlatform.Windows) ? "python.exe" : "python";
                var venvPython = Path.Combine(virtualEnv, scriptsDirectory, pythonExecutable);
                if (File.Exists(venvPython))
                {
                    _logger.LogInformation("Using Python interpreter from VIRTUAL_ENV: {Python}", venvPython);
                    return venvPython;
                }
            }

            var projectPython = TryResolveProjectPython();
            if (!string.IsNullOrWhiteSpace(projectPython))
            {
                return projectPython;
            }

            var candidates = new[] { "python", "python3", "py" };

            foreach (var candidate in candidates)
            {
                try
                {
                    var process = new Process
                    {
                        StartInfo = new ProcessStartInfo
                        {
                            FileName = candidate,
                            Arguments = "--version",
                            RedirectStandardOutput = true,
                            RedirectStandardError = true,
                            UseShellExecute = false,
                            CreateNoWindow = true
                        }
                    };

                    process.Start();
                    process.WaitForExit(5000);

                    if (process.ExitCode == 0)
                    {
                        _logger.LogInformation("Using Python interpreter discovered on PATH: {Python}", candidate);
                        return candidate;
                    }
                }
                catch
                {
                    continue;
                }
            }

            return null;
        }


        private string? TryResolveProjectPython()
        {
            try
            {
                var currentDirectory = Directory.GetCurrentDirectory();
                var venvRoot = Path.Combine(currentDirectory, ".venv");
                if (!Directory.Exists(venvRoot))
                {
                    return null;
                }

                var scriptsDirectory = RuntimeInformation.IsOSPlatform(OSPlatform.Windows) ? "Scripts" : "bin";
                var pythonExecutable = RuntimeInformation.IsOSPlatform(OSPlatform.Windows) ? "python.exe" : "python";
                var candidate = Path.Combine(venvRoot, scriptsDirectory, pythonExecutable);

                if (File.Exists(candidate))
                {
                    _logger.LogInformation("Using Python interpreter from project virtual environment: {Python}", candidate);
                    return candidate;
                }
            }
            catch (Exception ex)
            {
                _logger.LogDebug(ex, "Failed to resolve project virtual environment python executable.");
            }

            return null;
        }

        private (bool Success, string? Output, string? Error) ExecutePythonCommand(string command)
        {
            if (string.IsNullOrEmpty(_pythonExecutable))
            {
                return (false, null, "Python executable not set");
            }

            try
            {
                var process = new Process
                {
                    StartInfo = new ProcessStartInfo
                    {
                        FileName = _pythonExecutable,
                        Arguments = "-c",
                        RedirectStandardInput = true,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        UseShellExecute = false,
                        CreateNoWindow = true,
                        WorkingDirectory = Directory.GetCurrentDirectory()
                    }
                };

                process.Start();

                // Send the command to Python
                process.StandardInput.WriteLine(command);
                process.StandardInput.Close();

                var output = process.StandardOutput.ReadToEnd();
                var error = process.StandardError.ReadToEnd();

                process.WaitForExit(30000); // 30 second timeout

                return (process.ExitCode == 0, output, error);
            }
            catch (Exception ex)
            {
                return (false, null, ex.Message);
            }
        }

        protected virtual void Dispose(bool disposing)
        {
            if (!_disposed)
            {
                if (disposing)
                {
                    Shutdown();
                }
                _disposed = true;
            }
        }

        public void Dispose()
        {
            Dispose(disposing: true);
            GC.SuppressFinalize(this);
        }
    }

    /// <summary>
    /// Python bridge service implementation
    /// Provides high-level interface to Python simulation engine via processes
    /// </summary>
    public class PythonBridgeService : IPythonBridgeService
    {
        private readonly IPythonEngineService _pythonEngine;
        private readonly ILogger<PythonBridgeService> _logger;

        public event EventHandler<SimulationProgressEventArgs>? ProgressChanged;

        public PythonBridgeService(IPythonEngineService pythonEngine, ILogger<PythonBridgeService> logger)
        {
            _pythonEngine = pythonEngine;
            _logger = logger;
        }

        public async Task<SimulationResult> RunSimulationAsync(SimulationParameters parameters)
        {
            return await Task.Run(() =>
            {
                try
                {
                    _logger.LogInformation("Starting Python simulation...");

                    if (!_pythonEngine.IsInitialized)
                    {
                        return new SimulationResult
                        {
                            Success = false,
                            ErrorMessage = "Python engine not initialized"
                        };
                    }

                    // Create a simulation script
                    var parametersJson = JsonSerializer.Serialize(parameters);
                    var escapedJson = parametersJson.Replace("'", "\\'").Replace("\"", "\\\"");

                    var script = $@"
import json
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'src')

# Mock simulation for now - replace with actual simulation logic
parameters = json.loads(r'{escapedJson}')

result = {{
    'Success': True,
    'TimeSeries': [
        {{'Time': i * 0.01, 'Position': i * 0.001, 'Velocity': 0.1, 'Acceleration': 0.01, 'Force': 100.0, 'Pressure': 8.0}}
        for i in range(100)
    ],
    'Metrics': {{
        'MaxAcceleration': 0.1,
        'RmsAcceleration': 0.05,
        'MaxForce': 100.0,
        'PowerConsumption': 50.0,
        'ComfortIndex': 0.8,
        'StabilityIndex': 0.9
    }}
}}

print(json.dumps(result))
";

                    var result = _pythonEngine.ExecuteScript(script);

                    if (result == null)
                    {
                        return new SimulationResult
                        {
                            Success = false,
                            ErrorMessage = "No result from Python simulation"
                        };
                    }

                    try
                    {
                        var simulationResult = JsonSerializer.Deserialize<SimulationResult>(result.ToString()!);
                        _logger.LogInformation("Python simulation completed successfully");
                        return simulationResult ?? new SimulationResult { Success = false, ErrorMessage = "Failed to deserialize result" };
                    }
                    catch (JsonException ex)
                    {
                        _logger.LogError(ex, "Failed to deserialize simulation result");
                        return new SimulationResult
                        {
                            Success = false,
                            ErrorMessage = $"Deserialization error: {ex.Message}"
                        };
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error running Python simulation");
                    return new SimulationResult
                    {
                        Success = false,
                        ErrorMessage = ex.Message
                    };
                }
            });
        }

        public async Task<VisualizationData> GetVisualizationDataAsync()
        {
            return await Task.Run(() =>
            {
                try
                {
                    if (!_pythonEngine.IsInitialized)
                    {
                        return new VisualizationData();
                    }

                    // Mock visualization data for now
                    var script = @"
import json

result = {
    'GeometryObjects': [
        {
            'Name': 'Mass',
            'Type': 1,
            'Position': {'X': 0, 'Y': 0, 'Z': 0},
            'Rotation': {'X': 0, 'Y': 0, 'Z': 0},
            'Scale': {'X': 1, 'Y': 1, 'Z': 1},
            'Material': {'DiffuseColor': {'R': 200, 'G': 100, 'B': 100, 'A': 255}, 'Metallic': 0.3, 'Roughness': 0.7}
        }
    ],
    'Camera': {
        'Position': {'X': 5, 'Y': 5, 'Z': 5},
        'Target': {'X': 0, 'Y': 0, 'Z': 0},
        'Up': {'X': 0, 'Y': 1, 'Z': 0},
        'FieldOfView': 60
    },
    'Animation': []
}

print(json.dumps(result))
";

                    var result = _pythonEngine.ExecuteScript(script);

                    if (result == null)
                    {
                        return new VisualizationData();
                    }

                    try
                    {
                        return JsonSerializer.Deserialize<VisualizationData>(result.ToString()!) ?? new VisualizationData();
                    }
                    catch
                    {
                        return new VisualizationData();
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error getting visualization data from Python");
                    return new VisualizationData();
                }
            });
        }

        public async Task<bool> UpdateParametersAsync(SimulationParameters parameters)
        {
            return await Task.Run(() =>
            {
                try
                {
                    if (!_pythonEngine.IsInitialized)
                    {
                        return false;
                    }

                    var parametersJson = JsonSerializer.Serialize(parameters);
                    var escapedJson = parametersJson.Replace("'", "\\'").Replace("\"", "\\\"");

                    var script = $@"
import json
parameters = json.loads(r'{escapedJson}')
print('Parameters updated successfully')
";

                    var result = _pythonEngine.ExecuteScript(script);
                    return result != null;
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error updating parameters in Python");
                    return false;
                }
            });
        }

        private void OnProgressChanged(double progress, string status, TimeSeriesData? currentData = null)
        {
            ProgressChanged?.Invoke(this, new SimulationProgressEventArgs
            {
                Progress = progress,
                Status = status,
                CurrentData = currentData
            });
        }
    }
}
