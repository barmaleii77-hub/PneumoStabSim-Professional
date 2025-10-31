using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using System;
using System.Linq;
using System.Windows;
using PneumoStabSim.Core;

namespace PneumoStabSim
{
    /// <summary>
    /// Main entry point for PneumoStabSim Professional application
    /// Integrates with existing Python simulation engine
    /// </summary>
    public class Program
    {
        [STAThread]
        public static void Main(string[] args)
        {
            try
            {
                var host = CreateHostBuilder(args).Build();

                using (host)
                {
                    var logger = host.Services.GetRequiredService<ILogger<Program>>();
                    var environmentService = host.Services.GetRequiredService<IEnvironmentPreparationService>();
                    var environmentResult = environmentService.PrepareEnvironment();

                    if (!environmentResult.Success)
                    {
                        foreach (var error in environmentResult.Errors)
                        {
                            logger.LogError("Environment preparation error: {Error}", error);
                        }

                        var combinedErrors = string.Join(Environment.NewLine, environmentResult.Errors);
                        MessageBox.Show($"Environment preparation failed:{Environment.NewLine}{combinedErrors}",
                            "PneumoStabSim Professional",
                            MessageBoxButton.OK,
                            MessageBoxImage.Error);
                        return -1;
                    }

                    if (!string.IsNullOrWhiteSpace(environmentResult.PythonExecutablePath))
                    {
                        logger.LogInformation("Using Python interpreter {Python}", environmentResult.PythonExecutablePath);
                    }

                    if (environmentResult.Warnings.Any())
                    {
                        foreach (var warning in environmentResult.Warnings)
                        {
                            logger.LogWarning("Environment preparation warning: {Warning}", warning);
                        }
                    }

                    // Initialize Python engine integration
                    var pythonService = host.Services.GetRequiredService<IPythonEngineService>();
                    if (!pythonService.Initialize())
                    {
                        const string message = "Failed to initialise the embedded Python engine. Check the log output for details.";
                        logger.LogError(message);
                        MessageBox.Show(message,
                            "PneumoStabSim Professional",
                            MessageBoxButton.OK,
                            MessageBoxImage.Error);
                        return -1;
                    }

                    // Start WPF application
                    var app = new App();
                    app.InitializeComponent();

                    // Set up dependency injection in WPF
                    app.Services = host.Services;

                    return app.Run();
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Critical error during application startup: {ex.Message}",
                    "PneumoStabSim Professional",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
                return -1;
            }
        }

        private static IHostBuilder CreateHostBuilder(string[] args) =>
            Host.CreateDefaultBuilder(args)
                .ConfigureServices((context, services) =>
                {
                    // Core services
                    services.AddSingleton<IConfigurationService, ConfigurationService>();
                    services.AddSingleton<ILoggingService, LoggingService>();

                    // Environment preparation
                    services.AddSingleton<IEnvironmentPreparationService, EnvironmentPreparationService>();

                    // Python integration
                    services.AddSingleton<IPythonEngineService, PythonEngineService>();
                    services.AddSingleton<IPythonBridgeService, PythonBridgeService>();

                    // Data export service
                    services.AddScoped<IDataExportService, DataExportService>();
                })
                .ConfigureLogging((context, logging) =>
                {
                    logging.ClearProviders();
                    logging.AddConsole();
                    logging.AddDebug();
                    logging.SetMinimumLevel(LogLevel.Information);
                });
    }
}

/// <summary>
/// WPF Application class with dependency injection support
/// </summary>
public partial class App : Application
{
    public IServiceProvider? Services { get; set; }

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        // For now, show a simple message - main window will be implemented later
        MessageBox.Show("PneumoStabSim Professional v2.0.0\n\nPython integration initialized successfully!\n\nThis is a framework setup - UI components will be added next.",
            "PneumoStabSim Professional",
            MessageBoxButton.OK,
            MessageBoxImage.Information);

        // Exit for now - in real implementation would show main window
        Shutdown();
    }
}
