package com.faraday.backend.web;

import com.faraday.backend.domain.Conversation;
import com.faraday.backend.repo.ConversationRepository;
import com.faraday.backend.repo.MessageRepository;
import com.faraday.backend.security.CurrentUser;
import com.faraday.backend.web.dto.ConversationResponse;
import com.faraday.backend.web.dto.CreateConversationRequest;
import com.faraday.backend.web.dto.MessageResponse;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/conversations")
public class ConversationController {

    private final ConversationRepository conversationRepo;
    private final MessageRepository messageRepo;

    public ConversationController(
            ConversationRepository conversationRepo, MessageRepository messageRepo) {
        this.conversationRepo = conversationRepo;
        this.messageRepo = messageRepo;
    }

    @PostMapping
    public ConversationResponse create(@Valid @RequestBody CreateConversationRequest req) {
        Conversation conversation = new Conversation(CurrentUser.id(), req.title());
        conversationRepo.save(conversation);
        return ConversationResponse.from(conversation);
    }

    @GetMapping
    public List<ConversationResponse> list() {
        return conversationRepo.findByUserIdOrderByUpdatedAtDesc(CurrentUser.id())
                .stream().map(ConversationResponse::from).toList();
    }

    @GetMapping("/{id}")
    public ConversationResponse get(@PathVariable UUID id) {
        // findByIdAndUserId -> 404 (not 403) on a mismatch, so existence never leaks.
        Conversation conversation = conversationRepo.findByIdAndUserId(id, CurrentUser.id())
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        return ConversationResponse.from(conversation);
    }

    @GetMapping("/{id}/messages")
    public List<MessageResponse> messages(@PathVariable UUID id) {
        // Owner-check the conversation first (404 if not theirs), then list oldest-first.
        conversationRepo.findByIdAndUserId(id, CurrentUser.id())
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        return messageRepo.findByConversationIdOrderByCreatedAtAsc(id)
                .stream().map(MessageResponse::from).toList();
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable UUID id) {
        Conversation conversation = conversationRepo.findByIdAndUserId(id, CurrentUser.id())
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        conversationRepo.delete(conversation);
    }
}
