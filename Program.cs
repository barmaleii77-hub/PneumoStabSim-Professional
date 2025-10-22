using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
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
                    // Initialize Python engine integration
                    var pythonService = host.Services.GetRequiredService<IPythonEngineService>();
                    pythonService.Initialize();

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
