# Student Tablet Reset & Re-Enrollment

Runbook for IT operations staff supporting managed student tablets (Android and
iPad) enrolled in the school's Mobile Device Management (MDM) console.

## When to reset a student tablet

Reset a device when it is being reassigned to a new student, when it is stuck on a
forgotten passcode, when the MDM profile is corrupted, or when the device fails
compliance checks after a failed OS update. Do not reset a device that only has a
flat battery or a single misbehaving app — try a reboot or app reinstall first.

## How to reset a student tablet

1. Confirm the device's asset tag and current owner in the MDM console before
   doing anything destructive.
2. In the MDM console, select the device and trigger a **Wipe** (Android) or
   **Erase Device** (iPad). This performs a remote factory reset.
3. If the device is offline or unmanaged, perform a manual factory reset: power
   off, then hold Volume Down + Power (Android) or use Recovery Mode (iPad) and
   choose "Erase all content and settings".
4. Wait for the device to reboot to the out-of-box setup screen.
5. Connect it to the staff provisioning Wi-Fi (SSID `SCHOOL-PROV`).
6. Let the MDM enrollment profile push automatically; the device will re-download
   the standard app set and restrictions.
7. Re-assign the device to the new student record in the MDM console and re-apply
   the asset tag.

## Verifying a successful re-enrollment

Confirm the device shows as **Managed / Compliant** in the console, the standard
app catalog is installed, and the kiosk/restriction profile is active. Hand the
device back only after compliance is green.

## Common pitfalls

Activation Lock (iPad) or Factory Reset Protection (Android) will block setup if
the previous user's account was not removed first. Always remove the device from
the prior student's account before wiping, or you will need to clear the lock via
the vendor's Apple School Manager / Android Enterprise portal.
