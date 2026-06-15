package com.faraday.backend.web.dto;

import java.util.UUID;

public record UserResponse(UUID id, String email, String displayName, String role) {
}
