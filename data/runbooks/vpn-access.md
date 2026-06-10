# VPN Access & Troubleshooting

Runbook for granting and troubleshooting remote VPN access for staff connecting to
the internal network.

## Requesting VPN access

New staff request VPN access through the IT service desk ticket form. Access
requires an active directory account in good standing and manager approval. Once
approved, add the user to the `vpn-users` security group and issue the client
configuration profile.

## Installing the VPN client

1. Download the approved VPN client from the internal software portal.
2. Import the `.ovpn` profile sent by the service desk.
3. Sign in with your domain credentials plus the one-time MFA code from the
   authenticator app.

## Troubleshooting connection failures

If the client fails to connect, check the following in order:

1. Confirm the user is in the `vpn-users` group — group membership changes can take
   up to 15 minutes to replicate.
2. Verify the account is not locked out (see the account lockout runbook).
3. Check that MFA enrollment is complete; an unenrolled user is rejected at the
   authentication stage.
4. Confirm the client clock is accurate — time skew over 5 minutes breaks the MFA
   token validation.
5. Have the user try a different network; some hotel and captive-portal networks
   block the VPN UDP port (1194).

## Escalation

If authentication succeeds but no internal resources are reachable, escalate to
network engineering — this usually indicates a routing or split-tunnel policy
issue rather than a client problem.
