# sunsynk_alerts

## requirements:

pip install aiohttp
pip install requests

## Envorment Variables:
SUNSYNK_USER
SUNSYNK_PASS
BULKSMS_USER
BULKSMS_PASS

### Set with Windows:
Set-Item -Path "env:SUNSYNK_USER" -Value "hein@aerobots.co.za" -Force
Set-Item -Path "env:SUNSYNK_PASS" -Value [pwd] -Force
Set-Item -Path "env:BULKSMS_USER" -Value "aerobots" -Force
Set-Item -Path "env:BULKSMS_PASS" -Value [pwd] -Force

Confirm:
gci env:* | sort-object name