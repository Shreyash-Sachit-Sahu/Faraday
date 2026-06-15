package com.faraday.backend.repo;

import com.faraday.backend.domain.Document;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface DocumentRepository extends JpaRepository<Document, UUID> {

    List<Document> findByUserIdOrderByCreatedAtDesc(UUID userId);

    Optional<Document> findByIdAndUserId(UUID id, UUID userId);
}
