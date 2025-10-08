using Microsoft.Extensions.Logging;
using System.Text.Json;

namespace PneumoStabSim.Core
{
    /// <summary>
    /// Configuration service implementation
    /// </summary>
    public class ConfigurationService : IConfigurationService
    {
        private readonly Dictionary<string, object> _configuration = new();
        private readonly string _configPath;
        private readonly ILogger<ConfigurationService> _logger;

        public ConfigurationService(ILogger<ConfigurationService> logger)
        {
            _logger = logger;
            _configPath = Path.Combine(Directory.GetCurrentDirectory(), "config", "appsettings.json");
            LoadConfiguration();
        }

        public T GetValue<T>(string key, T defaultValue = default!)
        {
            try
            {
                if (_configuration.TryGetValue(key, out var value))
                {
                    if (value is T directValue)
                        return directValue;
                    
                    if (value is JsonElement jsonElement)
                        return jsonElement.Deserialize<T>() ?? defaultValue;
                    
                    return (T)Convert.ChangeType(value, typeof(T));
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, $"Error getting configuration value for key: {key}");
            }
            
            return defaultValue;
        }

        public void SetValue<T>(string key, T value)
        {
            _configuration[key] = value!;
        }

        public void SaveConfiguration()
        {
            try
            {
                var directory = Path.GetDirectoryName(_configPath);
                if (!string.IsNullOrEmpty(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                var json = JsonSerializer.Serialize(_configuration, new JsonSerializerOptions 
                { 
                    WriteIndented = true 
                });
                
                File.WriteAllText(_configPath, json);
                _logger.LogInformation($"Configuration saved to: {_configPath}");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to save configuration");
            }
        }

        public void LoadConfiguration()
        {
            try
            {
                if (File.Exists(_configPath))
                {
                    var json = File.ReadAllText(_configPath);
                    var config = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(json);
                    
                    if (config != null)
                    {
                        foreach (var kvp in config)
                        {
                            _configuration[kvp.Key] = kvp.Value;
                        }
                    }
                    
                    _logger.LogInformation($"Configuration loaded from: {_configPath}");
                }
                else
                {
                    _logger.LogInformation("Configuration file not found, using defaults");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to load configuration");
            }
        }
    }

    /// <summary>
    /// Logging service implementation
    /// </summary>
    public class LoggingService : ILoggingService
    {
        private readonly ILoggerFactory _loggerFactory;

        public LoggingService(ILoggerFactory loggerFactory)
        {
            _loggerFactory = loggerFactory;
        }

        public ILogger<T> GetLogger<T>()
        {
            return _loggerFactory.CreateLogger<T>();
        }

        public void LogInfo(string message)
        {
            var logger = _loggerFactory.CreateLogger<LoggingService>();
            logger.LogInformation(message);
        }

        public void LogWarning(string message)
        {
            var logger = _loggerFactory.CreateLogger<LoggingService>();
            logger.LogWarning(message);
        }

        public void LogError(string message, Exception? exception = null)
        {
            var logger = _loggerFactory.CreateLogger<LoggingService>();
            logger.LogError(exception, message);
        }
    }

    /// <summary>
    /// Data export service implementation
    /// </summary>
    public class DataExportService : IDataExportService
    {
        private readonly ILogger<DataExportService> _logger;

        public DataExportService(ILogger<DataExportService> logger)
        {
            _logger = logger;
        }

        public async Task ExportToCsvAsync(string filePath, IEnumerable<object> data)
        {
            try
            {
                var directory = Path.GetDirectoryName(filePath);
                if (!string.IsNullOrEmpty(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                using var writer = new StreamWriter(filePath);
                
                var dataList = data.ToList();
                if (dataList.Count == 0) return;

                // Write header based on first object properties
                var properties = dataList[0].GetType().GetProperties();
                var headers = string.Join(",", properties.Select(p => p.Name));
                await writer.WriteLineAsync(headers);

                // Write data rows
                foreach (var item in dataList)
                {
                    var values = properties.Select(p => p.GetValue(item)?.ToString() ?? "");
                    var row = string.Join(",", values);
                    await writer.WriteLineAsync(row);
                }

                _logger.LogInformation($"Data exported to CSV: {filePath}");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to export CSV: {filePath}");
                throw;
            }
        }

        public async Task ExportToJsonAsync(string filePath, object data)
        {
            try
            {
                var directory = Path.GetDirectoryName(filePath);
                if (!string.IsNullOrEmpty(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                var json = JsonSerializer.Serialize(data, new JsonSerializerOptions 
                { 
                    WriteIndented = true 
                });
                
                await File.WriteAllTextAsync(filePath, json);
                _logger.LogInformation($"Data exported to JSON: {filePath}");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to export JSON: {filePath}");
                throw;
            }
        }

        public async Task<byte[]> ExportToPdfAsync(object data)
        {
            // Placeholder implementation - would need PDF library
            await Task.Delay(100);
            
            var json = JsonSerializer.Serialize(data, new JsonSerializerOptions 
            { 
                WriteIndented = true 
            });
            
            return System.Text.Encoding.UTF8.GetBytes($"PDF Export Placeholder:\n{json}");
        }
    }
}
