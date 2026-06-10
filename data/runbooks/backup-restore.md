# File Server Backup & Restore

Runbook for the nightly file-server backup job and for restoring lost files.

## Backup schedule and retention

The file server runs an incremental backup every night at 02:00 and a full backup
every Sunday. Incrementals are retained for 30 days; full backups for 12 months.
Backups are written to the on-site NAS and replicated off-site each morning.

## Verifying a backup ran

1. Open the backup console and confirm last night's job shows **Completed**.
2. Check the job report for skipped or failed files.
3. Once a month, perform a test restore of a single file to confirm backups are
   actually recoverable — a backup you have never restored is not a backup.

## Restoring a deleted or corrupted file

1. Ask the user for the file path and the approximate date it was last known good.
2. In the backup console, browse to that path and select the most recent version
   from before the loss.
3. Restore to a staging folder, not directly over the live location, so you do not
   overwrite anything unexpectedly.
4. Verify the restored file opens correctly, then move it into place.
5. Notify the user and confirm the file is usable.

## Restoring after a server failure

For a full server loss, provision a replacement host, install the backup agent,
and run a bare-metal or volume-level restore from the most recent full plus
subsequent incrementals. Validate share permissions after the restore — they are a
common thing to be lost or reset.
