# Security Explained (No Jargon)

**GAP-66: Anti Crypto-Priesthood**

> "I bow before the authority of specialists... but I allow no one to impose it upon me." - Bakunin

This document explains how the Solarpunk mesh network protects you, in plain English. No unexplained jargon. No techno-mysticism.

---

## What We're Protecting

- **Your identity**: So only you can post as you
- **Your messages**: So only the recipient can read them
- **Your location**: So stalkers can't find you
- **Your relationships**: Who you exchange with
- **Your safety**: Emergency alerts, sanctuary locations

---

## How It Works

### 1. Encryption = Locked Boxes

When you send a message, it goes in a locked box. Only the recipient has the key.

**Even we can't read it.**

The message travels locked, and only unlocks when your friend opens it.

<details>
<summary>Technical details (click to expand)</summary>

**Technical name:** X25519 key exchange + XSalsa20-Poly1305 AEAD encryption

**What this means:** It's the same encryption used by Signal messenger. Mathematicians have spent decades trying to break this. They can't.

**How it works:**
1. Your phone generates a secret key (never shared)
2. Your phone generates a public key (shared with everyone)
3. When you message Bob, your phone combines your secret key + Bob's public key = shared secret
4. Message is encrypted with shared secret
5. Only Bob's phone can decrypt (his secret key + your public key = same shared secret)

**Security guarantee:** Even if someone intercepts the message, they can't read it without Bob's secret key, which never leaves his phone.
</details>

---

### 2. Signatures = Wax Seals

When you post an offer, it has your digital signature.

- No one can fake it
- No one can change it
- If someone tries to edit your offer, the seal breaks

<details>
<summary>Technical details (click to expand)</summary>

**Technical name:** Ed25519 digital signatures

**What this means:** When you post something, your phone creates a mathematical proof that:
1. YOU wrote it (not someone else)
2. It WASN'T changed (even a single letter)

**How it works:**
1. You write: "Offering tomatoes"
2. Your phone signs it with your secret key
3. Anyone can verify the signature with your public key
4. If someone changes it to "Offering money", the signature breaks

**Security guarantee:** Cryptographers have proven that without your secret key, creating a valid signature is mathematically impossible (would take billions of years even with all the world's computers).
</details>

---

### 3. Mesh Sync = Passing Notes

Messages hop phone-to-phone until they reach you.

Like kids passing notes in class. Works even when internet is down.

<details>
<summary>Technical details (click to expand)</summary>

**Technical name:** DTN (Delay-Tolerant Networking) with store-and-forward bundles

**What this means:** Your phone doesn't need to reach the recipient directly. Messages are passed along:

1. You create message → encrypted
2. Your phone sends to nearby phones
3. Those phones forward to their neighbors
4. Eventually reaches recipient
5. All encrypted the whole way

**Works offline:** As long as phones form a chain (even over days), the message gets through. Think of it like:
- You give letter to neighbor
- Neighbor gives to their friend
- Friend gives to recipient
- All sealed envelopes, no one reads the contents

**Security guarantee:** Each hop verifies signatures. If anyone tampers with the message, the signature breaks and it's rejected.
</details>

---

### 4. Web of Trust = Friend-of-Friend Verification

You vouch for people you know in real life. They vouch for people they know.

If you're 3+ friend-hops from someone, you probably don't trust them.

<details>
<summary>Technical details (click to expand)</summary>

**Technical name:** Decentralized Web of Trust with trust score computation

**How it works:**
1. Genesis nodes (organizers you know) start with 1.0 trust
2. When Alice vouches for Bob, Bob gets Alice's trust × 0.8
3. When Bob vouches for Carol, Carol gets Bob's trust × 0.8
4. Trust degrades with distance (prevents fake vouching chains)

**Why 0.8?** Research shows this balances:
- Growth (new people can join)
- Security (infiltrators can't fake deep chains)

**Example:**
- Genesis Alice: 1.0 trust
- Alice vouches for Bob: 0.8 trust
- Bob vouches for Carol: 0.64 trust
- Carol vouches for Dan: 0.51 trust
- Dan vouches for Eve: 0.41 trust (below 0.5 threshold for posting)

**Security guarantee:** To get trusted status, you need real relationships. Fake accounts can't bootstrap trust without real humans vouching.
</details>

---

## What This DOESN'T Protect

**Be honest about limitations:**

### 1. If someone steals your unlocked phone → they have your keys

**What to do:**
- Always lock your phone
- Use duress PIN (opens decoy app instead)
- Use panic wipe (5 taps on logo = instant data wipe)

### 2. If you share your password → anyone can impersonate you

**What to do:**
- Don't share your password
- Don't reuse passwords from other sites
- Use seed phrase backup (12 words you write down and keep safe)

### 3. Metadata (who talks to who, when) → visible to carriers

**What we hide:**
- Message content ✅ (encrypted)
- Who you're messaging ✅ (encrypted)

**What we CAN'T hide:**
- That you're using the app (phone carrier can see traffic)
- Approximate message size (they can see bytes sent)
- Timing (when messages were sent)

**What to do if this matters:**
- Use VPN to hide traffic from carrier
- Use Tor to hide IP address
- Meet in person for sensitive communication

### 4. If you screenshot and share → that's on you

**The app can't prevent:**
- Screenshots
- Taking photos of screen
- Sharing exported data

**What to do:**
- Don't screenshot sensitive messages
- Don't share sanctuary locations publicly
- Trust the people you're messaging

---

## Trust But Verify

We don't ask you to blindly trust us. You can check our work:

### For Everyone:
- **Open source code**: [GitHub repository](https://github.com/yourorg/solarpunk-mesh)
- **Security audits**: [Link to third-party audits]
- **How to report bugs**: [Responsible disclosure email]

### For Technical Users:
- **Cryptography specs**: [Link to technical documentation]
- **Audit the code**: [Instructions for code review]
- **Reproducible builds**: [Build from source instructions]
- **Verify signatures**: [How to check app signatures]

### For Cryptographers:
- **Threat model**: [Detailed threat analysis]
- **Crypto primitives**: Ed25519, X25519, XSalsa20-Poly1305, Argon2id
- **Key management**: [Technical key storage documentation]
- **Attack surface**: [Security architecture doc]

---

## Security Settings You Control

### 1. Your Security Level

```
Settings > Security > My Security Level

🔒 Basic (default)
   Messages encrypted, identity signed
   Good for: Most users

🔐 High
   + Require PIN for app unlock
   + Auto-lock after 5 minutes
   Good for: Anyone who shares their phone

🔥 Maximum
   + Duress PIN (opens decoy app)
   + Panic wipe (5 taps on logo)
   + Auto-delete old messages
   Good for: High-risk situations
```

### 2. What You Share

```
Settings > Privacy > What I Share

📍 Location: Never / Approximate / Exact
   Default: Approximate (city level)

👥 Connection List: Private / Friends / Public
   Default: Private (only you see your connections)

📊 Activity: Hidden / Visible to Cell / Public
   Default: Visible to Cell (your local community)
```

### 3. Who Can Contact You

```
Settings > Privacy > Who Can Message Me

Anyone: 0.3+ trust score
Trusted: 0.6+ trust score
Friends Only: People you vouched for
No One: Pause incoming messages

Default: Trusted (0.6+ trust)
```

---

## Emergency: If Your Phone Is Compromised

### Duress PIN

```
Normal PIN: Opens your actual app
Duress PIN: Opens decoy app (looks like calculator)
```

**When to use:**
- Border crossing
- Police demanding phone unlock
- Anyone forcing you to unlock

**What happens:**
- They see calculator app
- Your real data stays hidden
- You can reveal real app later with normal PIN

### Panic Wipe

```
5 taps on logo = Instant data wipe
```

**What gets deleted:**
- All messages
- All contacts
- All sanctuary locations
- All encryption keys

**What survives:**
- You can recover from seed phrase
- Network continues (data is distributed)

**When to use:**
- Phone about to be seized
- Immediate danger
- No time to manually delete

### Recovery

```
Settings > Backup > Seed Phrase

Write down 12 words. Keep them VERY safe.
Anyone with these words = full access to your account.
```

**If you lose phone:**
1. Get new phone
2. Install app
3. Enter seed phrase
4. Your identity recovers
5. Message history is gone (by design - forward secrecy)

---

## Accessibility Test

Before publishing any security docs, we ask:

1. ✅ Can a 15-year-old understand this?
2. ✅ Does it avoid techno-mysticism?
3. ✅ Does it empower or intimidate?
4. ✅ Does it admit limitations honestly?

If we fail any of these, we rewrite.

---

## Questions?

### "Is this really secure?"

Yes. We use the same encryption as Signal (which security experts trust). But perfect security doesn't exist. We're honest about limitations.

### "Can the government break this?"

**Content:** No. Not without your secret key (which never leaves your phone).

**Metadata:** Yes. They can see you're using the app, when, and approximate message sizes. Use VPN/Tor if this matters.

### "Can you read my messages?"

No. Mathematically impossible. We don't have your secret key.

### "What if you're lying?"

Check our code. It's open source. Bring a friend who knows cryptography. We welcome scrutiny.

### "This seems complicated. Can I just trust you?"

You can. But Bakunin would say: **Verify if you're able. Trust if you're not. But always know you have the right to verify.**

---

## Remember

**Security is not about magic. It's about math.**

The math is real. The protection is real. But so is your right to understand it.

> "I bow before the authority of specialists... but I allow no one to impose it upon me." - Bakunin

We explain what we do. You decide if you trust it.
