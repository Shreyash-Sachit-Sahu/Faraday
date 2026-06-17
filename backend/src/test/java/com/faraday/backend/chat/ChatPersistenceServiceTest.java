package com.faraday.backend.chat;

import com.faraday.backend.domain.Message;
import com.faraday.backend.domain.MessageRole;
import com.faraday.backend.repo.ConversationRepository;
import com.faraday.backend.repo.MessageRepository;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/** Unit test for the multi-turn history fetch — pure logic, no Spring context. */
class ChatPersistenceServiceTest {

    @Test
    void recentHistory_returnsLastNTurns_oldestFirst_asRoleContentMaps() {
        MessageRepository messageRepo = mock(MessageRepository.class);
        ConversationRepository conversationRepo = mock(ConversationRepository.class);
        UUID conv = UUID.randomUUID();
        when(messageRepo.findByConversationIdOrderByCreatedAtAsc(conv)).thenReturn(List.of(
                new Message(conv, MessageRole.USER, "q1"),
                new Message(conv, MessageRole.ASSISTANT, "a1"),
                new Message(conv, MessageRole.USER, "q2"),
                new Message(conv, MessageRole.ASSISTANT, "a2"),
                new Message(conv, MessageRole.USER, "q3")));

        ChatPersistenceService service = new ChatPersistenceService(conversationRepo, messageRepo);
        List<Map<String, String>> history = service.recentHistory(conv, 3);

        assertThat(history).hasSize(3);
        assertThat(history.get(0)).containsEntry("role", "user").containsEntry("content", "q2");
        assertThat(history.get(1)).containsEntry("role", "assistant").containsEntry("content", "a2");
        assertThat(history.get(2)).containsEntry("role", "user").containsEntry("content", "q3");
    }

    @Test
    void recentHistory_capsAtAvailableMessages() {
        MessageRepository messageRepo = mock(MessageRepository.class);
        ConversationRepository conversationRepo = mock(ConversationRepository.class);
        UUID conv = UUID.randomUUID();
        when(messageRepo.findByConversationIdOrderByCreatedAtAsc(conv))
                .thenReturn(List.of(new Message(conv, MessageRole.USER, "only")));

        ChatPersistenceService service = new ChatPersistenceService(conversationRepo, messageRepo);
        assertThat(service.recentHistory(conv, 6)).hasSize(1);
    }
}
