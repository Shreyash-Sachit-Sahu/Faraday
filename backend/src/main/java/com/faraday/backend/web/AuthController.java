package com.faraday.backend.web;

import com.faraday.backend.auth.AuthService;
import com.faraday.backend.auth.TokenPair;
import com.faraday.backend.web.dto.LoginRequest;
import com.faraday.backend.web.dto.RefreshRequest;
import com.faraday.backend.web.dto.RegisterRequest;
import com.faraday.backend.web.dto.TokenResponse;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/register")
    public TokenResponse register(@Valid @RequestBody RegisterRequest req) {
        return toResponse(authService.register(req.email(), req.password(), req.displayName()));
    }

    @PostMapping("/login")
    public TokenResponse login(@Valid @RequestBody LoginRequest req) {
        return toResponse(authService.login(req.email(), req.password()));
    }

    @PostMapping("/refresh")
    public TokenResponse refresh(@Valid @RequestBody RefreshRequest req) {
        return toResponse(authService.refresh(req.refreshToken()));
    }

    @PostMapping("/logout")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void logout(@Valid @RequestBody RefreshRequest req) {
        authService.logout(req.refreshToken());
    }

    private TokenResponse toResponse(TokenPair pair) {
        return new TokenResponse(
                pair.accessToken(), pair.refreshToken(), pair.expiresInSeconds());
    }
}
