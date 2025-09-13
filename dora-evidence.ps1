<#
  DORA Evidence Collector for vSphere

  Author : LT
  Version: 1.0
  Target : VMware vSphere 8 (ESXi & vCenter)
  Mode   : Read-only (auditor)
  Output : Console tables + end-of-run summary
           Optional CSV/JSON export if -Export and -OutFolder are specified
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$VCenter,
  [string]$Username,
  [securestring]$Password,

  # Evidence windows / thresholds
  [int]$DaysBack = 30,
  [int]$DatastoreMinFreePct = 15,
  [int]$SnapshotMaxAgeDays = 14,

  # Optional export
  [switch]$Export,
  [string]$OutFolder = ".\dora-evidence"
)

Write-Host "DORA Evidence Collector (READ ONLY)" -ForegroundColor Cyan
Write-Host "vCenter: $VCenter | Window: last $DaysBack day(s)" -ForegroundColor Yellow

# ---- Connect ----
try {
  if ($PSBoundParameters.ContainsKey('Username') -and $PSBoundParameters.ContainsKey('Password')) {
    $vi = Connect-VIServer -Server $VCenter -User $Username -Password $Password -ErrorAction Stop
  } else {
    $vi = Connect-VIServer -Server $VCenter -ErrorAction Stop
  }
} catch {
  Write-Error "Failed to connect to vCenter '$VCenter'. $_"
  exit 1
}

# ---- Evidence record helper ----
function New-Evidence {
  param(
    [string]$Category,  # Inventory, Logging, Security, Resilience, Events, Third-Party, Operational, Change, Control
    [string]$Scope,     # Object/cluster/host name
    [string]$Key,       # What we measured / short control name
    [string]$Value,     # Observed value
    [string]$Severity = 'Info',  # Info|Warn|Fail|Pass
    [string]$Ref = '',  # DORA ref (e.g., 9.4.c)
    [string]$Notes = ''
  )
  [pscustomobject]@{
    Timestamp = (Get-Date).ToString("s")
    Category  = $Category
    Scope     = $Scope
    Key       = $Key
    Value     = $Value
    Severity  = $Severity
    Ref       = $Ref
    Notes     = $Notes
  }
}
$ev = @()

# ---- Basic vCenter info ----
try {
  $svc = Get-View ServiceInstance
  $about = Get-View $svc.Content.About
  $scopeName = $about.FullName
  $ev += New-Evidence -Category 'Inventory' -Scope $scopeName -Key 'vCenter Version' -Value "$($about.Version) build $($about.Build)"
  $ev += New-Evidence -Category 'Inventory' -Scope $scopeName -Key 'API Type' -Value $about.ApiType
  $ev += New-Evidence -Category 'Inventory' -Scope $scopeName -Key 'API Version' -Value $about.ApiVersion
} catch {
  $ev += New-Evidence -Category 'Inventory' -Scope $VCenter -Key 'vCenter Info' -Value 'Error retrieving' -Severity 'Warn' -Notes "$_"
}

# ---- Cluster resilience (HA/DRS) ----
$clusters = Get-Cluster | Sort-Object Name
foreach ($c in $clusters) {
  $ev += New-Evidence -Category 'Resilience' -Scope $c.Name -Key 'vSphere HA Enabled' -Value $c.HAEnabled
  $ev += New-Evidence -Category 'Resilience' -Scope $c.Name -Key 'DRS Enabled'       -Value $c.DrsEnabled
  if ($c.DrsEnabled) {
    $ev += New-Evidence -Category 'Resilience' -Scope $c.Name -Key 'DRS Mode' -Value $c.DrsAutomationLevel
  }
}

# ---- ESXi / Host inventory & controls ----
$hosts = Get-VMHost | Sort-Object Name
foreach ($h in $hosts) {
  $ev += New-Evidence -Category 'Inventory' -Scope $h.Name -Key 'ESXi Version' -Value "$($h.Version) build $($h.Build)"
  $ev += New-Evidence -Category 'Inventory' -Scope $h.Name -Key 'CPU/Memory'   -Value "$([int]$h.NumCpu) pCPU / $([math]::Round($h.MemoryTotalGB,2)) GB"
  $ev += New-Evidence -Category 'Inventory' -Scope $h.Name -Key 'ConnectionState' -Value $h.ConnectionState

  # --- Time / NTP (9.2)
  $ntp = (Get-VMHostNtpServer -VMHost $h -ErrorAction SilentlyContinue) -join ','
  $timeSvcs = Get-VMHostService -VMHost $h | Where-Object { $_.Key -in @('ntpd','ptpd') -or $_.Label -match 'NTP|PTP' }
  $running = ($timeSvcs | Where-Object Running) -ne $null
  if (($ntp -ne '') -and $running) { $sevNT = 'Pass' } else { $sevNT = 'Warn' }
  $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'NTP configured & running' -Value "Servers=[$ntp]; Running=$running" -Severity $sevNT -Ref '9.2'

  # --- Syslog dir persistent (11.8)
  $logDir = (Get-AdvancedSetting -Entity $h -Name 'Syslog.global.logDir' -ErrorAction SilentlyContinue).Value
  if ($logDir -and $logDir.Trim()) { $sevLD = 'Pass' } else { $sevLD = 'Warn' }
  $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'Persistent log dir' -Value $logDir -Severity $sevLD -Ref '11.8' -Notes 'Expect datastore:[path]'

  # --- Syslog target(s) (11.8)
  $syslog = (Get-AdvancedSetting -Entity $h -Name 'Syslog.global.logHost' -ErrorAction SilentlyContinue).Value
  if ($syslog -and $syslog.Trim()) { $sevSL = 'Pass' } else { $sevSL = 'Warn' }
  $ev += New-Evidence -Category 'Logging' -Scope $h.Name -Key 'Syslog Target(s)' -Value $syslog -Severity $sevSL -Ref '11.8' -Notes 'Forward to SIEM/central log'

  # --- ESXi Shell & SSH services (9.4.c)
  $svc = Get-VMHostService -VMHost $h
  $ssh = $svc | Where-Object Key -eq 'TSM-SSH'
  $shl = $svc | Where-Object Key -eq 'TSM'
  if ($ssh) {
    $okSSH = (-not $ssh.Running -and $ssh.Policy -ne 'on')
    if ($okSSH) { $sevSSH = 'Pass' } else { $sevSSH = 'Warn' }
    $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'SSH disabled (stopped/not auto)' -Value "Running=$($ssh.Running); Policy=$($ssh.Policy)" -Severity $sevSSH -Ref '9.4.c'
  }
  if ($shl) {
    $okSHL = (-not $shl.Running -and $shl.Policy -ne 'on')
    if ($okSHL) { $sevSHL = 'Pass' } else { $sevSHL = 'Warn' }
    $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'ESXi Shell disabled' -Value "Running=$($shl.Running); Policy=$($shl.Policy)" -Severity $sevSHL -Ref '9.4.c'
  }

  # --- ESXi Firewall default (9.4.c) via esxcli
  try {
    $cli = Get-EsxCli -VMHost $h -V2
    $fw = ($cli.network.firewall.get.Invoke())
    if ($fw.Enabled) { $sevFWE = 'Info' } else { $sevFWE = 'Warn' }
    $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'Firewall enabled' -Value "$($fw.Enabled)" -Severity $sevFWE -Ref '9.4.c'
    $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'Firewall defaultAction' -Value "$($fw.DefaultAction)" -Severity 'Info' -Ref '9.4.c' -Notes 'Review policy: block by default per org policy'
  } catch {
    $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'Firewall status' -Value 'Error retrieving' -Severity 'Warn' -Ref '9.4.c' -Notes "$_"
  }

  # --- SSH hardening (9.3.a/9.4.c) via esxcli system ssh get (best effort)
  try {
    $cli = Get-EsxCli -VMHost $h -V2
    $sshget = $cli.system.ssh.get.Invoke()
    if ($sshget) {
      if ($sshget.X11Forwarding -ne $null) {
        if (-not $sshget.X11Forwarding) { $sevX11 = 'Pass' } else { $sevX11 = 'Warn' }
        $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'SSH X11 forwarding disabled' -Value $sshget.X11Forwarding -Severity $sevX11 -Ref '9.4.c'
      }
      if ($sshget.GatewayPorts -ne $null) {
        if (-not $sshget.GatewayPorts) { $sevGP = 'Pass' } else { $sevGP = 'Warn' }
        $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'SSH gateway ports disabled' -Value $sshget.GatewayPorts -Severity $sevGP -Ref '9.4.c'
      }
      if ($sshget.AllowTcpForwarding -ne $null) {
        if (-not $sshget.AllowTcpForwarding) { $sevTCP = 'Pass' } else { $sevTCP = 'Warn' }
        $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'SSH tunnels (TCP forwarding) disabled' -Value $sshget.AllowTcpForwarding -Severity $sevTCP -Ref '9.3.a/9.4.c'
      }
      if ($sshget.Protocol -ne $null) {
        if ("$($sshget.Protocol)" -match '2') { $sevP = 'Pass' } else { $sevP = 'Warn' }
        $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'SSH protocol is v2' -Value "$($sshget.Protocol)" -Severity $sevP -Ref '9.3.a'
      }
    } else {
      $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'SSH settings' -Value 'Unavailable via esxcli' -Severity 'Info' -Ref '9.3.a/9.4.c'
    }
  } catch {
    $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'SSH settings' -Value 'Error retrieving' -Severity 'Info' -Ref '9.3.a/9.4.c' -Notes "$_"
  }

  # --- Image Profile / VIB acceptance (9.4.e)
  try {
    $acc = Get-VMHostAcceptanceLevel -VMHost $h -ErrorAction Stop
    $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'VIB Acceptance Level' -Value $acc -Ref '9.4.e'
  } catch {
    $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'VIB Acceptance Level' -Value 'Error retrieving' -Severity 'Warn' -Ref '9.4.e' -Notes "$_"
  }

  # --- Core dump enabled (11.8) via esxcli
  try {
    $cli = Get-EsxCli -VMHost $h -V2
    $cdFile = $cli.system.coredump.file.get.Invoke()
    $cdNet  = $cli.system.coredump.network.get.Invoke()
    if ($cdFile -and $cdFile.Active) {
      $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'Core dump (file) active' -Value "Path=$($cdFile.Path); Active=$($cdFile.Active)" -Severity 'Pass' -Ref '11.8'
    } elseif ($cdNet -and $cdNet.Enabled) {
      $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'Core dump (network) active' -Value "IP=$($cdNet.NetworkServerIpAddress); Enabled=$($cdNet.Enabled)" -Severity 'Pass' -Ref '11.8'
    } else {
      $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'Core dump configured' -Value 'No active core dump target' -Severity 'Warn' -Ref '11.8'
    }
  } catch {
    $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'Core dump status' -Value 'Error retrieving' -Severity 'Warn' -Ref '11.8' -Notes "$_"
  }

  # --- DCUI.Access (9.4.c)
  $dcuiAcc = (Get-AdvancedSetting -Entity $h -Name 'DCUI.Access' -ErrorAction SilentlyContinue).Value
  if ($dcuiAcc -and $dcuiAcc -ne '*') { $sevDCUI = 'Info' } else { $sevDCUI = 'Warn' }
  $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'DCUI.Access list' -Value $dcuiAcc -Severity $sevDCUI -Ref '9.4.c' -Notes 'Expect restricted named accounts'

  # --- Inter-VM TPS / sharing (9.3.b/9.3.c)
  $tps1 = (Get-AdvancedSetting -Entity $h -Name 'Mem.ShareForceSalting' -ErrorAction SilentlyContinue).Value
  $tps2 = (Get-AdvancedSetting -Entity $h -Name 'sched.mem.pshare.enable' -ErrorAction SilentlyContinue).Value
  $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'TPS settings' -Value "Mem.ShareForceSalting=$tps1; pshare.enable=$tps2" -Severity 'Info' -Ref '9.3.b/9.3.c' -Notes 'Expect TPS disabled or salted'

  # --- ESX Admins AD group usage (9.3.b/9.4.d)
  $esxAdmins = (Get-AdvancedSetting -Entity $h -Name 'Config.HostAgent.plugins.hostsvc.esxAdminsGroup' -ErrorAction SilentlyContinue).Value
  if ([string]::IsNullOrWhiteSpace($esxAdmins)) {
    $valEA = 'Not set'
    $sevEA = 'Pass'
  } else {
    $valEA = $esxAdmins
    $sevEA = 'Warn'
  }
  $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'ESX Admins AD group' -Value $valEA -Severity $sevEA -Ref '9.3.b/9.4.d'

  # --- MOB disabled (9.3.b/9.4.c)
  $mob = (Get-AdvancedSetting -Entity $h -Name 'Config.HostAgent.plugins.solo.enableMob' -ErrorAction SilentlyContinue).Value
  if ($null -eq $mob) {
    $sevMOB = 'Info'
    $valMOB = 'Setting not present'
  } elseif ($mob -eq 'false' -or $mob -eq 0) {
    $sevMOB = 'Pass'
    $valMOB = "enableMob=$mob"
  } else {
    $sevMOB = 'Warn'
    $valMOB = "enableMob=$mob"
  }
  $ev += New-Evidence -Category 'Control' -Scope $h.Name -Key 'MOB disabled' -Value $valMOB -Severity $sevMOB -Ref '9.3.b/9.4.c'
}

# ---- Standard vSwitch Portgroups (VLAN 4095 + security) ----
$allStdPg = Get-VirtualPortGroup -Standard -ErrorAction SilentlyContinue
foreach ($pg in $allStdPg) {
  if ($pg.VlanId -eq 4095) {
    $ev += New-Evidence -Category 'Control' -Scope "$($pg.VMHost.Name)/$($pg.Name)" -Key 'VLAN 4095 in use' -Value 'Std PG' -Severity 'Warn' -Ref '9.4.c' -Notes 'VGT only if required'
  }
  $sec = $pg.ExtensionData.Spec.Policy.Security
  if ($sec) {
    if (-not $sec.AllowPromiscuous -and -not $sec.MacChanges -and -not $sec.ForgedTransmits) { $sevSPG = 'Pass' } else { $sevSPG = 'Warn' }
    $ev += New-Evidence -Category 'Control' -Scope "$($pg.VMHost.Name)/$($pg.Name)" -Key 'Std PG security (Reject all)' -Value "Promisc=$($sec.AllowPromiscuous); MACchg=$($sec.MacChanges); ForgedTx=$($sec.ForgedTransmits)" -Severity $sevSPG -Ref '9.4.b/9.4.c'
  }
}

# ---- vDS Portgroups (VLAN 4095 + security) ----
# (Fix: use .ExtensionData; handle trunk VLAN specs; null-safe policy reads)
$allVDpg = Get-VDPortgroup -ErrorAction SilentlyContinue
foreach ($vdpg in $allVDpg) {
  try {
    $conf = $vdpg.ExtensionData
    $cfg  = $conf.Config.DefaultPortConfig

    # VLAN detection
    $vlanSpec = $cfg.Vlan
    $vlanText = 'n/a'
    $vlan4095 = $false

    if ($vlanSpec -is [VMware.Vim.VmwareDistributedVirtualSwitchVlanIdSpec]) {
      $vlanText = "$($vlanSpec.VlanId)"
      if ($vlanSpec.VlanId -eq 4095) { $vlan4095 = $true }
    } elseif ($vlanSpec -is [VMware.Vim.VmwareDistributedVirtualSwitchTrunkVlanSpec]) {
      $ranges = @()
      foreach ($r in $vlanSpec.VlanId) { $ranges += ("{0}-{1}" -f $r.Start, $r.End) }
      $vlanText = "Trunk: " + ($ranges -join ',')
      foreach ($r in $vlanSpec.VlanId) { if ($r.Start -le 4095 -and $r.End -ge 4095) { $vlan4095 = $true; break } }
    }

    if ($vlan4095) {
      $ev += New-Evidence -Category 'Control' -Scope "$($vdpg.VDSwitch.Name)/$($vdpg.Name)" `
        -Key 'VLAN 4095 in use' -Value $vlanText -Severity 'Warn' -Ref '9.4.c' -Notes 'VGT only if required'
    }

    # Security policy
    $pm = $null; $mc = $null; $ft = $null
    if ($cfg.SecurityPolicy) {
      if ($cfg.SecurityPolicy.AllowPromiscuous) { $pm = $cfg.SecurityPolicy.AllowPromiscuous.Value }
      if ($cfg.SecurityPolicy.MacChanges)       { $mc = $cfg.SecurityPolicy.MacChanges.Value }
      if ($cfg.SecurityPolicy.ForgedTransmits)  { $ft = $cfg.SecurityPolicy.ForgedTransmits.Value }
    }
    $allReject = (-not $pm) -and (-not $mc) -and (-not $ft) -and ($pm -ne $null) -and ($mc -ne $null) -and ($ft -ne $null)
    if ($allReject) { $sevVDPG = 'Pass' } else { $sevVDPG = 'Warn' }
    $valText  = "Promisc=$pm; MACchg=$mc; ForgedTx=$ft"

    $ev += New-Evidence -Category 'Control' -Scope "$($vdpg.VDSwitch.Name)/$($vdpg.Name)" `
      -Key 'vDS PG security (Reject all)' -Value $valText -Severity $sevVDPG -Ref '9.4.b/9.4.c'
  }
  catch {
    $ev += New-Evidence -Category 'Control' -Scope "$($vdpg.VDSwitch.Name)/$($vdpg.Name)" `
      -Key 'vDS PG read' -Value 'Error' -Severity 'Warn' -Notes "$_"
  }
}

# ---- vDS NetFlow collectors (report) (9.3.a/9.4.c)
$allVDS = Get-VDSwitch -ErrorAction SilentlyContinue
foreach ($vds in $allVDS) {
  try {
    $vdsView = $vds | Get-View
    $nf = $vdsView.Config.IpfixConfig
    if ($nf) {
      $enabled = ($nf.CollectActiveFlow -or $nf.CollectObservationDomainId)
      $collector = "$($nf.CollectorIpAddress):$($nf.CollectorPort)"
      $ev += New-Evidence -Category 'Control' -Scope $vds.Name -Key 'NetFlow collector' -Value "$collector; Enabled=$enabled" -Severity 'Info' -Ref '9.3.a/9.4.c' -Notes 'Verify collector is authorized'
    }
  } catch {
    $ev += New-Evidence -Category 'Control' -Scope $vds.Name -Key 'NetFlow' -Value 'Error retrieving' -Severity 'Warn' -Ref '9.3.a/9.4.c' -Notes "$_"
  }
}

# ---- VM device controls (parallel/serial/CD) (9.4.c) – via Get-View (version-agnostic) ----
$allVMs = Get-VM -ErrorAction SilentlyContinue
foreach ($vm in $allVMs) {
  try {
    $v = Get-View -Id $vm.Id -Property Name,Config.Hardware.Device
    foreach ($dev in $v.Config.Hardware.Device) {
      # Parallel Port
      if ($dev -is [VMware.Vim.VirtualParallelPort]) {
        $connected = $dev.Connectable.Connected
        $startOn   = $dev.Connectable.StartConnected
        if ($connected -or $startOn) {
          $ev += New-Evidence -Category 'Control' -Scope $v.Name -Key 'Parallel device connected' `
            -Value ("Connected={0}; Start={1}" -f $connected,$startOn) -Severity 'Warn' -Ref '9.4.c'
        }
      }
      # Serial Port
      elseif ($dev -is [VMware.Vim.VirtualSerialPort]) {
        $connected = $dev.Connectable.Connected
        $startOn   = $dev.Connectable.StartConnected
        if ($connected -or $startOn) {
          $ev += New-Evidence -Category 'Control' -Scope $v.Name -Key 'Serial device connected' `
            -Value ("Connected={0}; Start={1}" -f $connected,$startOn) -Severity 'Warn' -Ref '9.4.c'
        }
      }
      # CD/DVD
      elseif ($dev -is [VMware.Vim.VirtualCdrom]) {
        $connected = $dev.Connectable.Connected
        $startOn   = $dev.Connectable.StartConnected
        $iso = $null
        if ($dev.Backing -is [VMware.Vim.VirtualCdromIsoBackingInfo]) {
          $iso = $dev.Backing.FileName
        } elseif ($dev.Backing -is [VMware.Vim.VirtualCdromRemotePassthroughBackingInfo]) {
          $iso = 'Remote Passthrough'
        } elseif ($dev.Backing -is [VMware.Vim.VirtualCdromAtapiBackingInfo]) {
          $iso = 'ATAPI Passthrough'
        } elseif ($dev.Backing -is [VMware.Vim.VirtualCdromSataBackingInfo]) {
          $iso = 'SATA Passthrough'
        }
        if ($connected -or $startOn) {
          $ev += New-Evidence -Category 'Control' -Scope $v.Name -Key 'CD/DVD connected' `
            -Value ("Connected={0}; Start={1}; ISO={2}" -f $connected,$startOn,$iso) -Severity 'Warn' -Ref '9.4.c'
        }
      }
    }
  } catch {
    $ev += New-Evidence -Category 'Control' -Scope $vm.Name -Key 'VM device scan' -Value 'Error retrieving' -Severity 'Warn' -Ref '9.4.c' -Notes "$_"
  }
}

# ---- Datastores (capacity/risk) ----
$dsList = Get-Datastore | Sort-Object Name
foreach ($ds in $dsList) {
  $freePct = [math]::Round(($ds.FreeSpaceGB / $ds.CapacityGB) * 100, 1)
  if ($freePct -lt $DatastoreMinFreePct) { $sevDS = 'Warn' } else { $sevDS = 'Info' }
  $ev += New-Evidence -Category 'Operational' -Scope $ds.Name -Key 'Free Space %' -Value "$freePct%" -Severity $sevDS -Notes "Threshold: $DatastoreMinFreePct%"
}

# ---- vCenter Extensions (3rd party / integrations) ----
try {
  $extMgr = Get-View ExtensionManager
  foreach ($ext in $extMgr.ExtensionList) {
    if ($ext.Version) { $ver = $ext.Version } else { $ver = 'n/a' }
    if ($ext.Description -and $ext.Description.Label) { $desc = $ext.Description.Label } else { $desc = 'n/a' }
    $ev += New-Evidence -Category 'Third-Party' -Scope $ext.Key -Key 'Extension' -Value "Version $ver; Desc=$desc"
  }
} catch {
  $ev += New-Evidence -Category 'Third-Party' -Scope $VCenter -Key 'Extensions' -Value 'Error retrieving' -Severity 'Warn' -Notes "$_"
}

# ---- Events & Alarms (last N days) ----
$since = (Get-Date).AddDays(-$DaysBack)
try {
  $events = Get-VIEvent -Start $since -MaxSamples 4000 -ErrorAction SilentlyContinue
  if ($events) {
    $crit = $events | Where-Object { $_.FullFormattedMessage -match '(?i)critical|alert' }
    $wrn  = $events | Where-Object { $_.FullFormattedMessage -match '(?i)warn' }
    $loginsOK  = $events | Where-Object { $_.GetType().Name -match 'UserLoginSessionEvent' }
    $loginsBad = $events | Where-Object { $_.GetType().Name -match 'BadUsernameSessionEvent|InvalidLogin' }

    $ev += New-Evidence -Category 'Events'   -Scope "Since $($since.ToString('yyyy-MM-dd'))" -Key 'Critical-like events (count)'  -Value ($crit.Count)
    $ev += New-Evidence -Category 'Events'   -Scope "Since $($since.ToString('yyyy-MM-dd'))" -Key 'Warning-like events (count)'   -Value ($wrn.Count)
    $ev += New-Evidence -Category 'Security' -Scope "Since $($since.ToString('yyyy-MM-dd'))" -Key 'Successful logins (count)'     -Value ($loginsOK.Count)

    if ($loginsBad.Count -gt 0) { $sevLogin = 'Warn' } else { $sevLogin = 'Info' }
    $ev += New-Evidence -Category 'Security' -Scope "Since $($since.ToString('yyyy-MM-dd'))" -Key 'Failed login attempts (count)' -Value ($loginsBad.Count) -Severity $sevLogin

    # Sample: recent config changes (top 10)
    $changes = $events | Where-Object { $_.GetType().Name -match 'TaskEvent|Reconfigure' } | Select-Object -First 10
    foreach ($ch in $changes) {
      if ($ch.UserName) { $userName = $ch.UserName } else { $userName = 'system' }
      $ev += New-Evidence -Category 'Change' -Scope $userName -Key ($ch.GetType().Name) -Value ($ch.FullFormattedMessage)
    }
  } else {
    $ev += New-Evidence -Category 'Events' -Scope "Since $($since.ToString('yyyy-MM-dd'))" -Key 'Events' -Value 'No events returned' -Severity 'Warn'
  }
} catch {
  $ev += New-Evidence -Category 'Events' -Scope "Since $($since.ToString('yyyy-MM-dd'))" -Key 'Event collection' -Value 'Error retrieving' -Severity 'Warn' -Notes "$_"
}

# ---- Present evidence ----
Write-Host ""
Write-Host "=== Evidence (overview) ===" -ForegroundColor Cyan
$ev | Sort-Object Category, Scope |
  Select-Object Timestamp, Category, Scope, Ref, Key, Value, Severity |
  Format-Table -AutoSize

# ---- Summary ----
$tot = $ev.Count
$pass = ($ev | Where-Object Severity -eq 'Pass').Count
$info = ($ev | Where-Object Severity -eq 'Info').Count
$warn = ($ev | Where-Object Severity -eq 'Warn').Count
$fail = ($ev | Where-Object Severity -eq 'Fail').Count

Write-Host "`n=== Evidence Summary (last $DaysBack day(s)) ===" -ForegroundColor Cyan
Write-Host "  Total records : $tot"
Write-Host "  Pass          : $pass"
Write-Host "  Info          : $info"
Write-Host "  Warnings      : $warn"
Write-Host "  Fails         : $fail"

# ---- Optional export ----
if ($Export) {
  try {
    New-Item -ItemType Directory -Path $OutFolder -ErrorAction SilentlyContinue | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $csv = Join-Path $OutFolder "dora-evidence-$($VCenter)-$stamp.csv"
    $json = Join-Path $OutFolder "dora-evidence-$($VCenter)-$stamp.json"
    $ev | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $csv
    $ev | ConvertTo-Json -Depth 6 | Out-File -FilePath $json -Encoding UTF8
    Write-Host "`nSaved evidence to:" -ForegroundColor Green
    Write-Host "  CSV : $csv"
    Write-Host "  JSON: $json"
  } catch {
    Write-Warning "Export failed: $_"
  }
}

# ---- Disconnect ----
Disconnect-VIServer -Server $vi -Confirm:$false | Out-Null
