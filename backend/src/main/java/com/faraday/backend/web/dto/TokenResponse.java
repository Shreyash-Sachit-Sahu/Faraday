package com.faraday.backend.web.dto;

public record TokenResponse(String accessToken, String refreshToken, long expiresInSeconds) {
}
