$PipelineScript = "$PSScriptRoot\DAILY_PIPELINE.py"
$TaskName = "NSE_Neutral_Straddle_Daily_Run"
$PythonExe = "python.exe"

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument $PipelineScript -WorkingDirectory $PSScriptRoot
$Trigger = New-ScheduledTaskTrigger -Daily -At "18:00"

Register-ScheduledTask -Action $Action -Trigger $Trigger -TaskName $TaskName -Description "Runs the NSE Neutral Straddle Daily Pipeline"

Write-Host "Scheduled task '$TaskName' registered successfully to run daily at 18:00."
