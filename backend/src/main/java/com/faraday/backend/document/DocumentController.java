package com.faraday.backend.document;

import com.faraday.backend.domain.Document;
import com.faraday.backend.repo.DocumentRepository;
import com.faraday.backend.security.CurrentUser;
import com.faraday.backend.web.dto.DocumentResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Stream;

@RestController
@RequestMapping("/api/documents")
public class DocumentController {

    private static final Logger log = LoggerFactory.getLogger(DocumentController.class);
    private static final Set<String> ALLOWED_EXT = Set.of("pdf", "txt", "md", "docx");

    private final DocumentRepository documentRepo;
    private final DocumentIngestService ingestService;
    private final Path uploadsDir;

    public DocumentController(
            DocumentRepository documentRepo, DocumentIngestService ingestService,
            @Value("${faraday.uploads.dir}") String uploadsDir) {
        this.documentRepo = documentRepo;
        this.ingestService = ingestService;
        this.uploadsDir = Path.of(uploadsDir);
    }

    @PostMapping
    public ResponseEntity<DocumentResponse> upload(@RequestParam("file") MultipartFile file) {
        UUID userId = CurrentUser.id();
        String original = file.getOriginalFilename();
        if (file.isEmpty() || original == null || original.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Empty file");
        }
        if (!ALLOWED_EXT.contains(extensionOf(original))) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Unsupported file type");
        }

        Document doc = new Document(userId, original);  // id assigned in constructor
        Path userDir = uploadsDir.resolve(userId.toString());
        Path stored = userDir.resolve(doc.getId() + "__" + sanitize(original));
        try {
            Files.createDirectories(userDir);
            file.transferTo(stored);
        } catch (IOException | IllegalStateException e) {
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Store failed");
        }

        documentRepo.save(doc);  // PENDING row
        ingestService.ingestAsync(doc.getId(), userId, stored, original);  // returns immediately
        return ResponseEntity.status(HttpStatus.ACCEPTED).body(DocumentResponse.from(doc));
    }

    @GetMapping
    public List<DocumentResponse> list() {
        return documentRepo.findByUserIdOrderByCreatedAtDesc(CurrentUser.id())
                .stream().map(DocumentResponse::from).toList();
    }

    @GetMapping("/{id}")
    public DocumentResponse get(@PathVariable UUID id) {
        Document doc = documentRepo.findByIdAndUserId(id, CurrentUser.id())
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        return DocumentResponse.from(doc);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable UUID id) {
        UUID userId = CurrentUser.id();
        Document doc = documentRepo.findByIdAndUserId(id, userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));

        deleteStoredFiles(userId, id);
        // Python delete (Qdrant points + graph nodes) BEFORE the row delete;
        // if it fails, still delete the row but log it.
        try {
            ingestService.deleteFromAi(userId, id);
        } catch (Exception e) {
            log.warn("AI delete failed for document {}; deleting row anyway", id, e);
        }
        documentRepo.delete(doc);
    }

    private void deleteStoredFiles(UUID userId, UUID documentId) {
        Path userDir = uploadsDir.resolve(userId.toString());
        if (!Files.isDirectory(userDir)) {
            return;
        }
        String prefix = documentId + "__";
        try (Stream<Path> entries = Files.list(userDir)) {
            entries.filter(p -> p.getFileName().toString().startsWith(prefix))
                    .forEach(p -> {
                        try {
                            Files.deleteIfExists(p);
                        } catch (IOException e) {
                            log.warn("could not delete stored file {}", p, e);
                        }
                    });
        } catch (IOException e) {
            log.warn("could not list uploads dir for {}", userId, e);
        }
    }

    private static String extensionOf(String filename) {
        int dot = filename.lastIndexOf('.');
        return dot >= 0 ? filename.substring(dot + 1).toLowerCase() : "";
    }

    private static String sanitize(String filename) {
        String base = filename.replaceAll("[\\\\/]", "_").replaceAll("[^a-zA-Z0-9._-]", "_");
        return base.length() > 200 ? base.substring(0, 200) : base;
    }
}
