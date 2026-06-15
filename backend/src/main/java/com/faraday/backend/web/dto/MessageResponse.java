package com.faraday.backend.web.dto;

import com.faraday.backend.domain.Message;

import java.time.Instant;
import java.util.UUID;

public record MessageResponse(
        UUID id, String role, String content, String sources, Instant createdAt) {

    public static MessageResponse from(Message m) {
        return new MessageResponse(
                m.getId(), m.getRole().name(), m.getContent(), m.getSources(), m.getCreatedAt());
    }
}
