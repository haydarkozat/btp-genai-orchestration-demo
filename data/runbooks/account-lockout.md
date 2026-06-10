# Active Directory Account Lockout Recovery

Runbook for diagnosing and resolving locked-out Active Directory (AD) user
accounts.

## Symptoms of a locked account

The user cannot sign in to their workstation, email, or VPN and sees a message
that the account is locked. Lockouts are triggered automatically after five
consecutive failed sign-in attempts within the lockout window.

## Unlocking an account

1. Verify the user's identity per the help-desk identity-verification policy.
2. In Active Directory Users and Computers (or the admin portal), open the user
   object and choose **Unlock account**.
3. If the user has genuinely forgotten the password, reset it and require a change
   at next sign-in.
4. Tell the user to sign out everywhere (phone email, VPN client, mapped drives)
   and sign back in with the new password.

## Finding the source of repeated lockouts

If an account keeps locking immediately after being unlocked, a stale credential
is replaying somewhere. Check, in order:

1. A mobile device with a saved old email password.
2. A mapped network drive or scheduled task running as the user.
3. A still-open RDP session on another machine.

Use the AD security event logs (event ID 4740) on the PDC emulator to find which
source host issued the failed attempts.

## Prevention

Encourage users to update saved passwords on all devices immediately after a
reset, and to use the self-service password reset portal where available.
