using System;
using Microsoft.Extensions.Logging;
using System.Collections.Generic;
using System.Collections.ObjectModel;

namespace PneumoStabSim.Core
{
    /// <summary>
    /// Configuration service for application settings
    /// </summary>
    public interface IConfigurationService
    {
        T GetValue<T>(string key, T defaultValue = default!);
        void SetValue<T>(string key, T value);
        void SaveConfiguration();
        void LoadConfiguration();
    }

    /// <summary>
    /// Logging service wrapper
    /// </summary>
    public interface ILoggingService
    {
        ILogger<T> GetLogger<T>();
        void LogInfo(string message);
        void LogWarning(string message);
        void LogError(string message, Exception? exception = null);
    }

    /// <summary>
    /// Service that prepares and validates the runtime environment for Windows/Visual Studio.
    /// </summary>
    public interface IEnvironmentPreparationService
    {
        EnvironmentPreparationResult PrepareEnvironment();
    }

    /// <summary>
    /// Result information returned by the environment preparation service.
    /// Captures success state, warnings, errors, and applied environment variables.
    /// </summary>
    public class EnvironmentPreparationResult
    {
        private readonly List<string> _warnings = new();
        private readonly List<string> _errors = new();
        private readonly Dictionary<string, string> _environmentVariables = new(StringComparer.OrdinalIgnoreCase);

        public EnvironmentPreparationResult()
        {
            AppliedEnvironmentVariables = new ReadOnlyDictionary<string, string>(_environmentVariables);
        }

        public bool Success => _errors.Count == 0;
        public IReadOnlyList<string> Warnings => _warnings;
        public IReadOnlyList<string> Errors => _errors;
        public IReadOnlyDictionary<string, string> AppliedEnvironmentVariables { get; }
        public string? PythonExecutablePath { get; private set; }
        public bool EnvironmentSynchronized { get; private set; }

        public void AddWarning(string warning)
        {
            if (!string.IsNullOrWhiteSpace(warning))
            {
                _warnings.Add(warning);
            }
        }

        public void AddError(string error)
        {
            if (!string.IsNullOrWhiteSpace(error))
            {
                _errors.Add(error);
            }
        }

        public void RecordAppliedVariable(string key, string value)
        {
            if (!string.IsNullOrWhiteSpace(key))
            {
                _environmentVariables[key] = value;
            }
        }

        public void SetPythonExecutable(string path)
        {
            PythonExecutablePath = path;
        }

        public void MarkEnvironmentSynchronized()
        {
            EnvironmentSynchronized = true;
        }
    }

    /// <summary>
    /// Python engine integration service
    /// </summary>
    public interface IPythonEngineService
    {
        bool Initialize();
        void Shutdown();
        object? ExecuteScript(string script);
        T? CallFunction<T>(string moduleName, string functionName, params object[] args);
        bool IsInitialized { get; }
    }

    /// <summary>
    /// Bridge service for communicating with Python simulation
    /// </summary>
    public interface IPythonBridgeService
    {
        Task<SimulationResult> RunSimulationAsync(SimulationParameters parameters);
        Task<VisualizationData> GetVisualizationDataAsync();
        Task<bool> UpdateParametersAsync(SimulationParameters parameters);
        event EventHandler<SimulationProgressEventArgs>? ProgressChanged;
    }

    /// <summary>
    /// Data export service
    /// </summary>
    public interface IDataExportService
    {
        Task ExportToCsvAsync(string filePath, IEnumerable<object> data);
        Task ExportToJsonAsync(string filePath, object data);
        Task<byte[]> ExportToPdfAsync(object data);
    }

    /// <summary>
    /// Simulation parameters for pneumatic system
    /// </summary>
    public class SimulationParameters
    {
        public double Mass { get; set; } = 1000.0; // kg
        public double SpringStiffness { get; set; } = 50000.0; // N/m
        public double DampingCoefficient { get; set; } = 2000.0; // N*s/m
        public double PneumaticPressure { get; set; } = 8.0; // bar
        public double CylinderDiameter { get; set; } = 0.08; // m
        public double StrokeLength { get; set; } = 0.2; // m
        public double SimulationTime { get; set; } = 10.0; // seconds
        public double TimeStep { get; set; } = 0.001; // seconds
        public List<RoadProfile> RoadProfiles { get; set; } = new();
    }

    /// <summary>
    /// Road profile data
    /// </summary>
    public class RoadProfile
    {
        public string Name { get; set; } = string.Empty;
        public List<double> Elevations { get; set; } = new();
        public double Distance { get; set; }
        public double Roughness { get; set; }
    }

    /// <summary>
    /// Simulation results
    /// </summary>
    public class SimulationResult
    {
        public bool Success { get; set; }
        public string? ErrorMessage { get; set; }
        public List<TimeSeriesData> TimeSeries { get; set; } = new();
        public PerformanceMetrics Metrics { get; set; } = new();
        public DateTime Timestamp { get; set; } = DateTime.Now;
    }

    /// <summary>
    /// Time series data point
    /// </summary>
    public class TimeSeriesData
    {
        public double Time { get; set; }
        public double Position { get; set; }
        public double Velocity { get; set; }
        public double Acceleration { get; set; }
        public double Force { get; set; }
        public double Pressure { get; set; }
    }

    /// <summary>
    /// Performance metrics
    /// </summary>
    public class PerformanceMetrics
    {
        public double MaxAcceleration { get; set; }
        public double RmsAcceleration { get; set; }
        public double MaxForce { get; set; }
        public double PowerConsumption { get; set; }
        public double ComfortIndex { get; set; }
        public double StabilityIndex { get; set; }
    }

    /// <summary>
    /// Visualization data for 3D rendering
    /// </summary>
    public class VisualizationData
    {
        public List<GeometryData> GeometryObjects { get; set; } = new();
        public CameraData Camera { get; set; } = new();
        public List<AnimationFrame> Animation { get; set; } = new();
    }

    /// <summary>
    /// 3D geometry data
    /// </summary>
    public class GeometryData
    {
        public string Name { get; set; } = string.Empty;
        public GeometryType Type { get; set; }
        public Vector3D Position { get; set; }
        public Vector3D Rotation { get; set; }
        public Vector3D Scale { get; set; } = new(1, 1, 1);
        public MaterialData Material { get; set; } = new();
    }

    /// <summary>
    /// Geometry types
    /// </summary>
    public enum GeometryType
    {
        Sphere,
        Cube,
        Cylinder,
        Mesh,
        Custom
    }

    /// <summary>
    /// 3D vector data
    /// </summary>
    public struct Vector3D
    {
        public double X { get; set; }
        public double Y { get; set; }
        public double Z { get; set; }

        public Vector3D(double x, double y, double z)
        {
            X = x;
            Y = y;
            Z = z;
        }
    }

    /// <summary>
    /// Material data for rendering
    /// </summary>
    public class MaterialData
    {
        public Color DiffuseColor { get; set; } = Color.FromRgb(128, 128, 128);
        public double Metallic { get; set; } = 0.0;
        public double Roughness { get; set; } = 0.5;
        public string? TexturePath { get; set; }
    }

    /// <summary>
    /// Color representation
    /// </summary>
    public struct Color
    {
        public byte R { get; set; }
        public byte G { get; set; }
        public byte B { get; set; }
        public byte A { get; set; }

        public static Color FromRgb(byte r, byte g, byte b) => new() { R = r, G = g, B = b, A = 255 };
        public static Color FromArgb(byte a, byte r, byte g, byte b) => new() { A = a, R = r, G = g, B = b };
    }

    /// <summary>
    /// Camera data for 3D view
    /// </summary>
    public class CameraData
    {
        public Vector3D Position { get; set; }
        public Vector3D Target { get; set; }
        public Vector3D Up { get; set; } = new(0, 1, 0);
        public double FieldOfView { get; set; } = 60.0;
    }

    /// <summary>
    /// Animation frame data
    /// </summary>
    public class AnimationFrame
    {
        public double Time { get; set; }
        public Dictionary<string, Transform> ObjectTransforms { get; set; } = new();
    }

    /// <summary>
    /// 3D transform data
    /// </summary>
    public class Transform
    {
        public Vector3D Position { get; set; }
        public Vector3D Rotation { get; set; }
        public Vector3D Scale { get; set; } = new(1, 1, 1);
    }

    /// <summary>
    /// Simulation progress event arguments
    /// </summary>
    public class SimulationProgressEventArgs : EventArgs
    {
        public double Progress { get; set; } // 0.0 to 1.0
        public string Status { get; set; } = string.Empty;
        public TimeSeriesData? CurrentData { get; set; }
    }
}
