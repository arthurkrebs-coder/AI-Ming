using System.Diagnostics;
using System.IO;
using Vestris.ResourceLib;

public class ExecutableManager
{
   
    public static VersionResource? LoadResourceTable(string exe, Action<string> onStatus)
    {
        try
        {
            System.Windows.Application.Current.Dispatcher.Invoke(() => onStatus?.Invoke($"Load resources"));

            var versionResource = new VersionResource();
            versionResource.LoadFrom(exe);
            return versionResource;
        }
        catch (Exception e)
        {
            System.Windows.Application.Current.Dispatcher.Invoke(() => onStatus?.Invoke($"Error: {e.Message}"));
            return null;
        }
    }

    // NOTE: the old ChangeResourceTable (rewrite version resources to random strings) and
    // LoadAssemblyViaStream (Assembly.Load from an in-memory byte[]) were removed: both were dead code,
    // and both are textbook dropper/packer heuristics that antivirus engines flag statically — their mere
    // presence in the binary contributed to false-positive detections.

    public static string? FindExecutable()
    {
        string launcherExe = Environment.ProcessPath
            ?? Process.GetCurrentProcess().MainModule?.FileName
            ?? throw new InvalidOperationException("Não foi possível identificar o Launcher.exe.");
        string currentDir = Path.GetDirectoryName(launcherExe) ?? AppContext.BaseDirectory;

        var exeList = Directory.EnumerateFiles(currentDir, "*.exe")
            .Where(x => !string.Equals(x, launcherExe, StringComparison.OrdinalIgnoreCase))
            .Where(x => !string.Equals(Path.GetFileName(x), "createdump.exe", StringComparison.OrdinalIgnoreCase))
            .Where(x => !string.Equals(Path.GetFileName(x), "Installer.exe", StringComparison.OrdinalIgnoreCase))
            .OrderBy(x => x, StringComparer.OrdinalIgnoreCase)
            .ToList();

        if (exeList.Count == 1)
            return exeList[0];

        // Accept the PowerAim build names (including e.g. AIM-Botox), even if
        // the folder also contains unrelated helper executables.
        string[] knownNames = Core.Constants.Names
            .Select(n => new string(n.Where(c => !char.IsWhiteSpace(c)).ToArray()))
            .ToArray();
        string? namedExe = exeList.FirstOrDefault(file =>
            knownNames.Contains(Path.GetFileNameWithoutExtension(file), StringComparer.OrdinalIgnoreCase));
        if (namedExe != null)
            return namedExe;

        // Fallback for existing installations where the original launcher renamed
        // the app executable to a random eight-character filename.
        return exeList.FirstOrDefault(n => Path.GetFileNameWithoutExtension(n).Length == 8);
    }

    /// <summary>
    /// Start the locally built application without renaming its executable.
    /// Renaming the executable on every launch caused confusing file names and
    /// could interfere with security software. Returns a visible error when
    /// the process cannot start or exits immediately.
    /// </summary>
    public static async Task<string?> StartExecutable(string exe, Action<string>? onStatus = null)
    {
        if (!File.Exists(exe))
            return "O executável do PowerAim não foi encontrado. Confira os arquivos extraídos e o Histórico de Proteção do Windows.";

        try
        {
            string workingDirectory = Path.GetDirectoryName(exe) ?? AppContext.BaseDirectory;
            onStatus?.Invoke("Iniciando " + Path.GetFileName(exe) + "...");
            using var process = Process.Start(new ProcessStartInfo(exe)
            {
                UseShellExecute = true,
                WorkingDirectory = workingDirectory
            });

            if (process is null)
                return "O Windows não iniciou o PowerAim. Confira o Histórico de Proteção e as permissões do arquivo.";

            await Task.Delay(2500);
            if (process.HasExited)
            {
                string message = $"O PowerAim foi encerrado após iniciar (código {process.ExitCode}). Consulte o Visualizador de Eventos do Windows ou o arquivo de diagnóstico.";
                Launcher.StartupDiagnostics.Report("App closed immediately", message);
                return message;
            }
            return null;
        }
        catch (Exception ex)
        {
            Launcher.StartupDiagnostics.Report("Start app process", ex);
            return "Não foi possível iniciar o PowerAim: " + ex.Message;
        }
    }

}
