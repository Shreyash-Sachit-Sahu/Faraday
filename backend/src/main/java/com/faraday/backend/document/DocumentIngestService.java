package com.faraday.backend.document;

import com.faraday.backend.repo.DocumentRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.MediaType;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;

import java.nio.file.Path;
import java.util.Map;
import java.util.UUID;

@Service
public class DocumentIngestService {

    private final RestClient restClient;
    private final DocumentRepository documentRepo;

    public DocumentIngestService(
            @Value("${faraday.ai.base-url}") String baseUrl, DocumentRepository documentRepo) {
        this.restClient = RestClient.builder().baseUrl(baseUrl).build();
        this.documentRepo = documentRepo;
    }

    @Async("ingestExecutor")
    public void ingestAsync(UUID documentId, UUID userId, Path storedFile, String filename) {
        try {
            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("file", new FileSystemResource(storedFile));
            body.add("owner_id", userId.toString());
            body.add("doc_id", documentId.toString());

            Map<?, ?> resp = restClient.post()
                    .uri("/ingest")
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(body)
                    .retrieve()
                    .body(Map.class);

            int count = resp != null && resp.get("chunk_count") != null
                    ? ((Number) resp.get("chunk_count")).intValue() : 0;
            updateStatus(documentId, count > 0 ? "INDEXED" : "FAILED", count);
        } catch (Exception e) {
            updateStatus(documentId, "FAILED", 0);
        }
    }

    /** Remove the document's Qdrant points + graph nodes from the AI service. */
    public void deleteFromAi(UUID userId, UUID documentId) {
        restClient.delete()
                .uri(builder -> builder.path("/documents")
                        .queryParam("owner_id", userId.toString())
                        .queryParam("doc_id", documentId.toString())
                        .build())
                .retrieve()
                .toBodilessEntity();
    }

    @Transactional
    public void updateStatus(UUID documentId, String status, int chunkCount) {
        // Explicit save(): ingestAsync self-invokes this method, which bypasses the
        // @Transactional proxy (Spring AOP self-invocation), so a dirty-checking flush
        // would never fire. save() persists the transition regardless of the boundary.
        documentRepo.findById(documentId).ifPresent(doc -> {
            doc.setStatus(status);
            doc.setChunkCount(chunkCount);
            documentRepo.save(doc);
        });
    }
}
