using System.IO;
using System.Windows;
using PowerAim.AILogic;
using PowerAim.Config;
using PowerAim.Theme;

namespace PowerAim;

/// <summary>
/// Interaction logic for App.xaml
/// </summary>
public partial class App : System.Windows.Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        // Startup problems in a Windows GUI app do not always appear on screen.
        // Log them before the process shuts down so local builds can be diagnosed.
        DispatcherUnhandledException += (_, args) =>
        {
            RecordFatalError("Unhandled WPF exception", args.Exception);
            args.Handled = true;
            ShowStartupError(args.Exception);
            Shutdown(1);
        };
        AppDomain.CurrentDomain.UnhandledException += (_, args) =>
        {
            RecordFatalError("Fatal app exception",
                args.ExceptionObject as Exception ?? new Exception(args.ExceptionObject?.ToString()));
        };

        base.OnStartup(e);
        try
        {
            ThemeManager.Initialize();
        // Boot the OCR sampler — it ticks whenever OcrSettings.Enabled is true and
        // gracefully no-ops when no regions are configured or eng.traineddata is missing.
        OcrService.Instance.Start();
        // Best-effort load of the persisted AutoPlay learning model. Failures are silent —
        // the model just starts empty and the recorder fills it over time.
        try { AutoPlayLearningModel.Instance.Load(AppConfig.Current?.AutoPlayLearningSettings?.ModelPath); }
        catch { /* ignored */ }
        // Controller-mapping engine: KB↔Pad cross-mapping. Self-gates on profile presence,
        // so booting always is cheap. ViGEm bus driver is only required if the user enables
        // a profile with gamepad targets.
        PowerAim.InputLogic.Mapping.MappingEngine.Instance.Start();
        }
        catch (Exception ex)
        {
            RecordFatalError("PowerAim startup", ex);
            ShowStartupError(ex);
            Shutdown(1);
        }
    }

    private static void RecordFatalError(string stage, Exception ex)
    {
        try
        {
            var folder = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "PowerAim");
            Directory.CreateDirectory(folder);
            File.AppendAllText(Path.Combine(folder, "poweraim-errors.log"),
                $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {stage}{Environment.NewLine}{ex}{Environment.NewLine}{Environment.NewLine}");
        }
        catch { /* crash logging must not throw */ }
    }

    private static void ShowStartupError(Exception ex)
    {
        try
        {
            MessageBox.Show(
                "O PowerAim não conseguiu iniciar.\\n\\n".Replace("\\\\n", "\\n") + ex.Message +
                "\\n\\nDetalhes em %LOCALAPPDATA%\\PowerAim\\poweraim-errors.log",
                "PowerAim — Falha de inicialização",
                MessageBoxButton.OK, MessageBoxImage.Error);
        }
        catch { /* the windowing subsystem may already be unavailable */ }
    }

    protected override void OnExit(ExitEventArgs e)
    {
        OcrService.Instance.Stop();
        PowerAim.InputLogic.Mapping.MappingEngine.Instance.Dispose();
        base.OnExit(e);
    }

    public string ReadEmbeddedResource(string resourceName)
    {
        var assembly = typeof(App).Assembly;

        string defaultNamespace = typeof(App).Namespace;
        string fullResourceName = $"{defaultNamespace}.{resourceName}";

        using Stream stream = assembly.GetManifestResourceStream(fullResourceName)
            ?? throw new Exception("Resource not found: " + fullResourceName);

        using var reader = new StreamReader(stream);
        return reader.ReadToEnd();
    }
}