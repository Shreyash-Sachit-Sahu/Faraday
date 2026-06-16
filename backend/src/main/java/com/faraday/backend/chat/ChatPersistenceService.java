package com.faraday.backend.chat;

import com.faraday.backend.domain.Conversation;
import com.faraday.backend.domain.Message;
import com.faraday.backend.domain.MessageRole;
import com.faraday.backend.repo.ConversationRepository;
import com.faraday.backend.repo.MessageRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Persistence for the streaming chat proxy. Each method is its own short
 * transaction, invoked cross-bean from ChatController so the @Transactional
 * proxy applies (including on the reactor-netty completion thread).
 */
@Service
public class ChatPersistenceService {

    private final ConversationRepository conversationRepo;
    private final MessageRepository messageRepo;

    public ChatPersistenceService(
            ConversationRepository conversationRepo, MessageRepository messageRepo) {
        this.conversationRepo = conversationRepo;
        this.messageRepo = messageRepo;
    }

    @Transactional
    public Conversation resolveConversation(UUID userId, UUID conversationId, String firstMessage) {
        if (conversationId != null) {
            return conversationRepo.findByIdAndUserId(conversationId, userId)
                    .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        }
        String title = firstMessage.length() > 60 ? firstMessage.substring(0, 60) : firstMessage;
        return conversationRepo.save(new Conversation(userId, title));
    }

    @Transactional
    public void saveUserMessage(UUID conversationId, String content) {
        messageRepo.save(new Message(conversationId, MessageRole.USER, content));
    }

    /**
     * The last {@code maxMessages} messages of a conversation as {role, content}
     * turns (oldest-first), for multi-turn context. Call BEFORE saving the
     * current user message so it isn't included.
     */
    @Transactional(readOnly = true)
    public List<Map<String, String>> recentHistory(UUID conversationId, int maxMessages) {
        List<Message> all = messageRepo.findByConversationIdOrderByCreatedAtAsc(conversationId);
        int from = Math.max(0, all.size() - maxMessages);
        List<Map<String, String>> turns = new ArrayList<>();
        for (Message m : all.subList(from, all.size())) {
            turns.add(Map.of(
                    "role", m.getRole() == MessageRole.USER ? "user" : "assistant",
                    "content", m.getContent()));
        }
        return turns;
    }

    @Transactional
    public void saveAssistantMessage(UUID conversationId, String content, String sourcesJson) {
        Message message = new Message(conversationId, MessageRole.ASSISTANT, content);
        if (sourcesJson != null) {
            message.setSources(sourcesJson);
        }
        messageRepo.save(message);
        conversationRepo.findById(conversationId).ifPresent(conversation -> {
            conversation.touch();
            conversationRepo.save(conversation);
        });
    }
}
