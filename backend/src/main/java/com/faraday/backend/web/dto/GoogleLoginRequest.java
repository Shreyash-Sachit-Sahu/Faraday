package com.faraday.backend.web.dto;

import jakarta.validation.constraints.NotBlank;

public record GoogleLoginRequest(
        @NotBlank String idToken) {
}
