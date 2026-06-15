package com.faraday.backend.web.dto;

import com.faraday.backend.domain.Document;

import java.util.UUID;

public record DocumentResponse(UUID id, String filename, String status, int chunkCount) {

    public static DocumentResponse from(Document d) {
        return new DocumentResponse(
                d.getId(), d.getFilename(), d.getStatus(), d.getChunkCount());
    }
}
