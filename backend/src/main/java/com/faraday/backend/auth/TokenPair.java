package com.faraday.backend.auth;

public record TokenPair(String accessToken, String refreshToken, long expiresInSeconds) {
}
