package com.faraday.backend.auth;

import com.faraday.backend.domain.AuthProvider;
import com.faraday.backend.domain.RefreshToken;
import com.faraday.backend.domain.User;
import com.faraday.backend.repo.RefreshTokenRepository;
import com.faraday.backend.repo.UserRepository;
import com.faraday.backend.security.GoogleTokenVerifier;
import com.faraday.backend.security.JwtService;
import com.faraday.backend.security.TokenHasher;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.LockedException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.Instant;

@Service
// noRollbackFor: the verbatim login/refresh cores write (failed-attempt
// increment, lockout, family-burn revoke) and THEN throw these auth
// exceptions. Default rollback-on-RuntimeException would undo those security
// writes, so they must be excluded from rollback while still returning 401/423.
@Transactional(noRollbackFor = { BadCredentialsException.class, LockedException.class })
public class AuthService {

    private final UserRepository userRepo;
    private final RefreshTokenRepository refreshRepo;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final GoogleTokenVerifier googleTokenVerifier;
    private final int maxFailed;
    private final long lockoutMinutes;
    private final long refreshTtlDays;
    private final long accessTtlSeconds;

    public AuthService(
            UserRepository userRepo,
            RefreshTokenRepository refreshRepo,
            PasswordEncoder passwordEncoder,
            JwtService jwtService,
            GoogleTokenVerifier googleTokenVerifier,
            @Value("${faraday.auth.max-failed}") int maxFailed,
            @Value("${faraday.auth.lockout-minutes}") long lockoutMinutes,
            @Value("${faraday.jwt.refresh-ttl-days}") long refreshTtlDays,
            @Value("${faraday.jwt.access-ttl-seconds}") long accessTtlSeconds) {
        this.userRepo = userRepo;
        this.refreshRepo = refreshRepo;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.googleTokenVerifier = googleTokenVerifier;
        this.maxFailed = maxFailed;
        this.lockoutMinutes = lockoutMinutes;
        this.refreshTtlDays = refreshTtlDays;
        this.accessTtlSeconds = accessTtlSeconds;
    }

    // --- Google sign-in: verify ID token, find-or-create a GOOGLE user.
    // Reject a same-email LOCAL collision (no silent auto-link = no takeover). ---
    public TokenPair loginWithGoogle(String idToken) {
        var payload = googleTokenVerifier.verify(idToken);
        String sub = payload.getSubject();
        String email = payload.getEmail().toLowerCase();
        String name = (String) payload.get("name");

        var existing = userRepo.findByAuthProviderAndProviderSubject(AuthProvider.GOOGLE, sub);
        if (existing.isPresent()) {
            return issueTokens(existing.get());
        }
        if (userRepo.existsByEmail(email)) {
            throw new BadCredentialsException(
                    "An account with this email already exists. Sign in with your password.");
        }
        String displayName = (name != null && !name.isBlank()) ? name : email;
        User user = new User(email, null, displayName, AuthProvider.GOOGLE, "USER");
        user.setProviderSubject(sub);
        userRepo.save(user);
        return issueTokens(user);
    }

    // --- register: clear duplicate-email error (register UX favors clarity over
    // strict no-enumeration); a concurrent insert race is caught by the DB unique
    // constraint, which the exception handler also maps to 409. ---
    public TokenPair register(String email, String rawPassword, String displayName) {
        String normalized = email.toLowerCase();
        if (userRepo.existsByEmail(normalized)) {
            throw new DataIntegrityViolationException("Email already registered");
        }
        User user = new User(
                normalized, passwordEncoder.encode(rawPassword), displayName,
                AuthProvider.LOCAL, "USER");
        userRepo.save(user);
        return issueTokens(user);
    }

    // --- login: generic errors (no enumeration), lockout after N failures ---
    public TokenPair login(String email, String rawPassword) {
        User user = userRepo.findByEmail(email.toLowerCase()).orElse(null);
        if (user == null || user.getPasswordHash() == null) {
            // unknown email OR an OAuth-only account: identical generic failure
            throw new BadCredentialsException("Invalid email or password");
        }
        if (user.getLockoutUntil() != null && user.getLockoutUntil().isAfter(Instant.now())) {
            throw new LockedException("Account temporarily locked. Try again later.");
        }
        if (!passwordEncoder.matches(rawPassword, user.getPasswordHash())) {
            int attempts = user.getFailedLoginAttempts() + 1;
            if (attempts >= maxFailed) {
                user.setLockoutUntil(Instant.now().plus(Duration.ofMinutes(lockoutMinutes)));
                user.setFailedLoginAttempts(0);
            } else {
                user.setFailedLoginAttempts(attempts);
            }
            userRepo.save(user);
            throw new BadCredentialsException("Invalid email or password");
        }
        user.setFailedLoginAttempts(0);
        user.setLockoutUntil(null);
        userRepo.save(user);
        return issueTokens(user);
    }

    // --- refresh: rotate, and detect reuse of a revoked token ---
    public TokenPair refresh(String rawRefresh) {
        String hash = TokenHasher.sha256Hex(rawRefresh);
        RefreshToken token = refreshRepo.findByTokenHash(hash)
                .orElseThrow(() -> new BadCredentialsException("Invalid refresh token"));

        if (token.isRevoked()) {
            // A revoked token was presented -> likely theft. Burn the whole family.
            refreshRepo.revokeAllForUser(token.getUserId());
            throw new BadCredentialsException("Refresh token reuse detected");
        }
        if (token.getExpiresAt().isBefore(Instant.now())) {
            throw new BadCredentialsException("Refresh token expired");
        }

        User user = userRepo.findById(token.getUserId())
                .orElseThrow(() -> new BadCredentialsException("Invalid refresh token"));

        String newRaw = TokenHasher.newOpaqueToken();
        RefreshToken rotated = new RefreshToken(
                user.getId(), TokenHasher.sha256Hex(newRaw),
                Instant.now().plus(Duration.ofDays(refreshTtlDays)));
        token.setRevoked(true);
        token.setReplacedBy(rotated.getId());
        refreshRepo.save(token);
        refreshRepo.save(rotated);

        String access = jwtService.generateAccessToken(
                user.getId(), user.getEmail(), user.getRole());
        return new TokenPair(access, newRaw, accessTtlSeconds);
    }

    // --- logout: revoke the presented refresh token (idempotent) ---
    public void logout(String rawRefresh) {
        String hash = TokenHasher.sha256Hex(rawRefresh);
        refreshRepo.findByTokenHash(hash).ifPresent(token -> {
            token.setRevoked(true);
            refreshRepo.save(token);
        });
    }

    private TokenPair issueTokens(User user) {
        String access = jwtService.generateAccessToken(
                user.getId(), user.getEmail(), user.getRole());
        String rawRefresh = TokenHasher.newOpaqueToken();
        RefreshToken refresh = new RefreshToken(
                user.getId(), TokenHasher.sha256Hex(rawRefresh),
                Instant.now().plus(Duration.ofDays(refreshTtlDays)));
        refreshRepo.save(refresh);
        return new TokenPair(access, rawRefresh, accessTtlSeconds);
    }
}
