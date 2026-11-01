using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Threading;
using System.Windows.Forms;

namespace JorwalNimSetup
{
    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            ServicePointManager.SecurityProtocol = (SecurityProtocolType)3072; // Tls12
            Application.Run(new InstallerForm());
        }
    }

    public class InstallerForm : Form
    {
        private TextBox txtFolder;
        private Button btnBrowse;
        private Button btnInstall;
        private ProgressBar progressBar;
        private Label lblStatus;
        private TextBox txtLog;
        private CheckBox chkDesktopShortcut;
        private CheckBox chkLaunchAfter;

        private string defaultPath;

        public InstallerForm()
        {
            InitializeComponent();
        }

        private void InitializeComponent()
        {
            this.Text = "JORWAL NIM — Setup Wizard";
            this.Size = new Size(580, 480);
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.StartPosition = FormStartPosition.CenterScreen;
            this.BackColor = Color.FromArgb(24, 24, 27);
            this.ForeColor = Color.White;

            defaultPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "jorwal-nim");

            // Header Banner
            Panel headerPanel = new Panel();
            headerPanel.Dock = DockStyle.Top;
            headerPanel.Height = 70;
            headerPanel.BackColor = Color.FromArgb(16, 185, 129); // Accent Emerald
            this.Controls.Add(headerPanel);

            Label lblTitle = new Label();
            lblTitle.Text = "JORWAL NIM Setup";
            lblTitle.Font = new Font("Segoe UI", 14, FontStyle.Bold);
            lblTitle.ForeColor = Color.White;
            lblTitle.Location = new Point(20, 12);
            lblTitle.AutoSize = true;
            headerPanel.Controls.Add(lblTitle);

            Label lblSub = new Label();
            lblSub.Text = "Autonomous AI Drug Discovery Platform — Autonomous Setup";
            lblSub.Font = new Font("Segoe UI", 9, FontStyle.Regular);
            lblSub.ForeColor = Color.FromArgb(240, 253, 244);
            lblSub.Location = new Point(22, 40);
            lblSub.AutoSize = true;
            headerPanel.Controls.Add(lblSub);

            // Folder Selection Label
            Label lblSelect = new Label();
            lblSelect.Text = "Destination Folder:";
            lblSelect.Font = new Font("Segoe UI", 9, FontStyle.Bold);
            lblSelect.Location = new Point(25, 90);
            lblSelect.AutoSize = true;
            this.Controls.Add(lblSelect);

            txtFolder = new TextBox();
            txtFolder.Location = new Point(25, 115);
            txtFolder.Size = new Size(410, 25);
            txtFolder.Font = new Font("Segoe UI", 9);
            txtFolder.Text = defaultPath;
            txtFolder.BackColor = Color.FromArgb(39, 39, 42);
            txtFolder.ForeColor = Color.White;
            this.Controls.Add(txtFolder);

            btnBrowse = new Button();
            btnBrowse.Text = "Browse...";
            btnBrowse.Location = new Point(445, 114);
            btnBrowse.Size = new Size(95, 27);
            btnBrowse.Font = new Font("Segoe UI", 9);
            btnBrowse.BackColor = Color.FromArgb(63, 63, 70);
            btnBrowse.ForeColor = Color.White;
            btnBrowse.FlatStyle = FlatStyle.Flat;
            btnBrowse.Click += BtnBrowse_Click;
            this.Controls.Add(btnBrowse);

            // Checkboxes
            chkDesktopShortcut = new CheckBox();
            chkDesktopShortcut.Text = "Create Desktop Shortcut";
            chkDesktopShortcut.Checked = true;
            chkDesktopShortcut.Location = new Point(25, 155);
            chkDesktopShortcut.AutoSize = true;
            this.Controls.Add(chkDesktopShortcut);

            chkLaunchAfter = new CheckBox();
            chkLaunchAfter.Text = "Launch Cockpit immediately after setup completes";
            chkLaunchAfter.Checked = true;
            chkLaunchAfter.Location = new Point(220, 155);
            chkLaunchAfter.AutoSize = true;
            this.Controls.Add(chkLaunchAfter);

            // Progress Bar
            progressBar = new ProgressBar();
            progressBar.Location = new Point(25, 190);
            progressBar.Size = new Size(515, 20);
            progressBar.Style = ProgressBarStyle.Continuous;
            this.Controls.Add(progressBar);

            lblStatus = new Label();
            lblStatus.Text = "Ready to install. Click 'Install' to begin.";
            lblStatus.Font = new Font("Segoe UI", 9, FontStyle.Italic);
            lblStatus.ForeColor = Color.FromArgb(161, 161, 170);
            lblStatus.Location = new Point(25, 218);
            lblStatus.Size = new Size(515, 20);
            this.Controls.Add(lblStatus);

            // Log Console
            txtLog = new TextBox();
            txtLog.Location = new Point(25, 245);
            txtLog.Size = new Size(515, 135);
            txtLog.Multiline = true;
            txtLog.ReadOnly = true;
            txtLog.ScrollBars = ScrollBars.Vertical;
            txtLog.BackColor = Color.FromArgb(15, 15, 18);
            txtLog.ForeColor = Color.FromArgb(52, 211, 153);
            txtLog.Font = new Font("Consolas", 8.5f);
            this.Controls.Add(txtLog);

            // Install Button
            btnInstall = new Button();
            btnInstall.Text = "Install & Launch";
            btnInstall.Location = new Point(395, 395);
            btnInstall.Size = new Size(145, 34);
            btnInstall.Font = new Font("Segoe UI", 10, FontStyle.Bold);
            btnInstall.BackColor = Color.FromArgb(16, 185, 129);
            btnInstall.ForeColor = Color.White;
            btnInstall.FlatStyle = FlatStyle.Flat;
            btnInstall.Click += BtnInstall_Click;
            this.Controls.Add(btnInstall);
        }

        private void BtnBrowse_Click(object sender, EventArgs e)
        {
            using (FolderBrowserDialog fbd = new FolderBrowserDialog())
            {
                fbd.Description = "Select Installation Directory for JORWAL NIM";
                fbd.SelectedPath = txtFolder.Text;
                if (fbd.ShowDialog() == DialogResult.OK)
                {
                    txtFolder.Text = fbd.SelectedPath;
                }
            }
        }

        private void Log(string msg)
        {
            if (this.InvokeRequired)
            {
                this.Invoke(new Action<string>(Log), msg);
                return;
            }
            txtLog.AppendText(msg + Environment.NewLine);
        }

        private void SetStatus(string msg, int progress)
        {
            if (this.InvokeRequired)
            {
                this.Invoke(new Action<string, int>(SetStatus), msg, progress);
                return;
            }
            lblStatus.Text = msg;
            if (progress >= 0 && progress <= 100)
            {
                progressBar.Value = progress;
            }
        }

        private void BtnInstall_Click(object sender, EventArgs e)
        {
            btnInstall.Enabled = false;
            btnBrowse.Enabled = false;
            txtFolder.Enabled = false;

            string targetDir = txtFolder.Text.Trim();
            if (string.IsNullOrEmpty(targetDir))
            {
                MessageBox.Show("Please specify a target installation folder.", "Invalid Folder", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                btnInstall.Enabled = true;
                btnBrowse.Enabled = true;
                txtFolder.Enabled = true;
                return;
            }

            Thread t = new Thread(() => RunInstallation(targetDir));
            t.IsBackground = true;
            t.Start();
        }

        private void RunInstallation(string targetDir)
        {
            try
            {
                SetStatus("Creating target directory...", 10);
                Log("[1/6] Destination: " + targetDir);
                if (!Directory.Exists(targetDir))
                {
                    Directory.CreateDirectory(targetDir);
                }

                // Check if serve_cockpit.py is already present in targetDir or parent directory
                string servePy = Path.Combine(targetDir, "serve_cockpit.py");
                string parentServePy = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "serve_cockpit.py");
                if (!File.Exists(servePy) && File.Exists(parentServePy))
                {
                    targetDir = Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", ".."));
                    servePy = Path.Combine(targetDir, "serve_cockpit.py");
                    Log("[1/6] Detected local repository at: " + targetDir);
                }

                if (!File.Exists(servePy))
                {
                    SetStatus("Downloading JORWAL NIM source archive...", 25);
                    Log("[2/6] Fetching repository archive...");
                    string zipPath = Path.Combine(Path.GetTempPath(), "jorwal-nim.zip");
                    string extractPath = Path.Combine(Path.GetTempPath(), "jorwal-nim-extract");

                    using (WebClient wc = new WebClient())
                    {
                        try
                        {
                            wc.DownloadFile("https://github.com/Jorwalzzz/bionemo-nim-benchmark/archive/refs/heads/main.zip", zipPath);
                        }
                        catch
                        {
                            wc.DownloadFile("https://github.com/Jorwalzzz/bionemo-agentic-scientist/archive/refs/heads/main.zip", zipPath);
                        }
                    }

                    if (Directory.Exists(extractPath)) Directory.Delete(extractPath, true);
                    ZipFile.ExtractToDirectory(zipPath, extractPath);

                    string[] subDirs = Directory.GetDirectories(extractPath);
                    string sourceDir = subDirs.Length > 0 ? subDirs[0] : extractPath;

                    // Copy all files
                    CopyDirectory(sourceDir, targetDir);

                    // Cleanup temp
                    if (File.Exists(zipPath)) File.Delete(zipPath);
                    if (Directory.Exists(extractPath)) Directory.Delete(extractPath, true);
                    Log("[2/6] Files unpacked successfully.");
                }
                else
                {
                    Log("[2/6] Existing JORWAL NIM files detected in target folder.");
                }

                SetStatus("Configuring offline runtime environment...", 50);
                Log("[3/6] Setting up offline configuration (.env)...");
                string envFile = Path.Combine(targetDir, ".env");
                if (!File.Exists(envFile))
                {
                    File.WriteAllText(envFile, "USE_MOCK=true\nDISABLE_TRIAL_LIMIT=true\nNVIDIA_API_KEY=\n");
                    Log("      Created .env with zero-cost Mock Mode enabled.");
                }

                SetStatus("Executing automated setup & dependency bootstrap...", 75);
                Log("[4/6] Bootstrapping Python & dependencies via install.bat...");

                string installBat = Path.Combine(targetDir, "install.bat");
                if (!File.Exists(installBat))
                {
                    installBat = Path.Combine(targetDir, "scripts", "installers", "install.bat");
                }

                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = installBat;
                psi.Arguments = "--setup-wizard";
                psi.WorkingDirectory = targetDir;
                psi.CreateNoWindow = true;
                psi.UseShellExecute = false;
                psi.RedirectStandardOutput = true;
                psi.RedirectStandardError = true;

                using (Process proc = Process.Start(psi))
                {
                    proc.OutputDataReceived += (s, ev) => { if (ev.Data != null) Log("  " + ev.Data); };
                    proc.ErrorDataReceived += (s, ev) => { if (ev.Data != null) Log("  " + ev.Data); };
                    proc.BeginOutputReadLine();
                    proc.BeginErrorReadLine();
                    proc.WaitForExit();
                }

                SetStatus("Creating shortcuts...", 90);
                Log("[5/6] Finalizing shortcuts...");
                string runBat = Path.Combine(targetDir, "run.bat");

                if (chkDesktopShortcut.Checked)
                {
                    try
                    {
                        string desktopPath = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
                        string shortcutPath = Path.Combine(desktopPath, "JORWAL NIM Cockpit.url");
                        using (StreamWriter writer = new StreamWriter(shortcutPath))
                        {
                            writer.WriteLine("[InternetShortcut]");
                            writer.WriteLine("URL=http://localhost:8000");
                            writer.WriteLine("IconIndex=0");
                        }
                        Log("      Created Desktop link: JORWAL NIM Cockpit.url");
                    }
                    catch (Exception ex)
                    {
                        Log("      Shortcut error: " + ex.Message);
                    }
                }

                SetStatus("Installation Complete!", 100);
                Log("[6/6] Setup completed successfully!");

                if (chkLaunchAfter.Checked)
                {
                    Log("Launching JORWAL NIM Cockpit in browser...");
                    Process.Start(new ProcessStartInfo
                    {
                        FileName = runBat,
                        WorkingDirectory = targetDir,
                        UseShellExecute = true
                    });
                }

                this.Invoke(new Action(() =>
                {
                    MessageBox.Show(this, "JORWAL NIM has been successfully installed and configured!\n\nLocation: " + targetDir, "Installation Complete", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    this.Close();
                }));
            }
            catch (Exception ex)
            {
                Log("[ERROR] " + ex.ToString());
                SetStatus("Error during setup: " + ex.Message, 0);
                this.Invoke(new Action(() =>
                {
                    MessageBox.Show(this, "An error occurred during installation:\n\n" + ex.Message, "Setup Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    btnInstall.Enabled = true;
                    btnBrowse.Enabled = true;
                    txtFolder.Enabled = true;
                }));
            }
        }

        private static void CopyDirectory(string sourceDir, string targetDir)
        {
            foreach (string dir in Directory.GetDirectories(sourceDir, "*", SearchOption.AllDirectories))
            {
                Directory.CreateDirectory(dir.Replace(sourceDir, targetDir));
            }
            foreach (string file in Directory.GetFiles(sourceDir, "*.*", SearchOption.AllDirectories))
            {
                string dest = file.Replace(sourceDir, targetDir);
                File.Copy(file, dest, true);
            }
        }
    }
}
