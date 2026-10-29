using System;
using System.Windows;

namespace Launcher
{
    /// <summary>Application entry point with visible diagnostics for fatal WPF startup errors.</summary>
    public partial class App : System.Windows.Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
            DispatcherUnhandledException += (_, args) =>
            {
                StartupDiagnostics.Report("Unhandled launcher UI exception", args.Exception);
                args.Handled = true;
                try
                {
                    MessageBox.Show(
                        "O Launcher encontrou um erro e não conseguiu continuar.\n\n" +
                        args.Exception.Message + "\n\nDetalhes em:\n" + StartupDiagnostics.LogFile,
                        "PowerAim — Erro ao iniciar", MessageBoxButton.OK, MessageBoxImage.Error);
                }
                catch { /* Windows UI may be unavailable */ }
                Shutdown(1);
            };
            AppDomain.CurrentDomain.UnhandledException += (_, args) =>
            {
                StartupDiagnostics.Report("Fatal launcher exception", args.ExceptionObject?.ToString() ?? "Unknown error");
            };
            base.OnStartup(e);
        }
    }
}
