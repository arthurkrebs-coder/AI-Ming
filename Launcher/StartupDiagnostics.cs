using System;
using System.IO;

namespace Launcher;

/// <summary>
/// Persist launcher startup errors so a double-click that displays no UI can be diagnosed.
/// Never throw from diagnostic logging itself.
/// </summary>
internal static class StartupDiagnostics
{
    public static string LogFile => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "PowerAim", "launcher-errors.log");

    public static void Report(string phase, Exception error) => Report(phase, error.ToString());

    public static void Report(string phase, string details)
    {
        try
        {
            string file = LogFile;
            string? dir = Path.GetDirectoryName(file);
            if (!string.IsNullOrWhiteSpace(dir)) Directory.CreateDirectory(dir);
            File.AppendAllText(file,
                $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {phase}{Environment.NewLine}{details}{Environment.NewLine}{Environment.NewLine}");
        }
        catch
        {
            // Diagnostics must never crash the app.
        }
    }
}
