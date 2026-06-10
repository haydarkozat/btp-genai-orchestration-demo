# Network Printer & Print Queue Issues

Runbook for resolving the most common shared-printer and print-queue problems in
classrooms and staff rooms.

## Jobs stuck in the print queue

When print jobs pile up and nothing prints:

1. On the print server, open the queue for the affected printer.
2. Cancel all stuck jobs.
3. Stop the Print Spooler service, clear the `spool\PRINTERS` folder, then start
   the service again.
4. Send a test page from the server to confirm the queue drains.

## Printer offline or not found

1. Confirm the printer is powered on and shows a ready status on its panel.
2. Ping the printer's IP address from the print server; no response means a network
   or power issue, not a driver issue.
3. If the IP has changed (common after a DHCP lease change), update the printer
   port to the new address or assign a DHCP reservation so it stays fixed.
4. Re-share the printer if clients still cannot see it.

## Poor print quality

Streaks or faded output usually mean a low toner cartridge or a dirty drum. Replace
consumables before assuming a hardware fault. Run the printer's built-in cleaning
cycle for inkjet devices.

## Escalation

If a printer repeatedly drops off the network despite a fixed reservation,
escalate to network engineering to check the switch port and cabling.
