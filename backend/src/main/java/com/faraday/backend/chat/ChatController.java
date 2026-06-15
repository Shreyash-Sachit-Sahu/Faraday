package com.faraday.backend.chat;

import com.faraday.backend.domain.Conversation;
import com.faraday.backend.security.CurrentUser;
import com.faraday.backend.web.dto.ChatRequest;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@RestController
public class ChatController {

    private final ChatPersistenceService persistence;
    private final AiServiceClient aiClient;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public ChatController(ChatPersistenceService persistence, AiServiceClient aiClient) {
        this.persistence = persistence;
        this.aiClient = aiClient;
    }

    @PostMapping("/api/chat")
    public SseEmitter chat(@Valid @RequestBody ChatRequest req) {
        UUID userId = CurrentUser.id();
        SseEmitter emitter = new SseEmitter(120_000L);

        // 1) resolve/create conversation + save USER message synchronously, up front
        Conversation conv = persistence.resolveConversation(userId, req.conversationId(), req.message());
        persistence.saveUserMessage(conv.getId(), req.message());

        // tell the client the conversation id (important for a brand-new conversation)
        sendQuietly(emitter, "meta", "{\"conversationId\":\"" + conv.getId() + "\"}");

        StringBuilder answer = new StringBuilder();
        List<String> sourcesJson = new ArrayList<>();
        List<String> ownerIds = List.of("global", userId.toString());

        aiClient.streamChat(req.message(), ownerIds).subscribe(
            event -> {
                String name = event.event();
                String data = event.data();
                sendQuietly(emitter, name, data);
                if ("token".equals(name) && data != null) {
                    answer.append(extractTokenText(data));   // parse {"text":"..."}
                } else if ("sources".equals(name) && data != null) {
                    sourcesJson.add(data);
                }
            },
            error -> emitter.completeWithError(error),       // user message already saved
            () -> {
                persistence.saveAssistantMessage(
                    conv.getId(), answer.toString(),
                    sourcesJson.isEmpty() ? null : sourcesJson.get(0));
                try { emitter.send(SseEmitter.event().name("done").data("{}")); } catch (IOException ignored) {}
                emitter.complete();
            }
        );
        return emitter;
    }

    private void sendQuietly(SseEmitter emitter, String name, String data) {
        try {
            SseEmitter.SseEventBuilder builder = SseEmitter.event().data(data == null ? "" : data);
            if (name != null) {
                builder.name(name);
            }
            emitter.send(builder);
        } catch (IOException e) {
            emitter.completeWithError(e);  // client disconnected
        }
    }

    private String extractTokenText(String json) {
        try {
            JsonNode node = objectMapper.readTree(json);
            JsonNode text = node.get("text");
            return text != null ? text.asText() : "";
        } catch (Exception e) {
            return "";
        }
    }
}
