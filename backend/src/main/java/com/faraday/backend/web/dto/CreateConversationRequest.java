package com.faraday.backend.web.dto;

import jakarta.validation.constraints.Size;

public record CreateConversationRequest(
        @Size(max = 200) String title) {
}
