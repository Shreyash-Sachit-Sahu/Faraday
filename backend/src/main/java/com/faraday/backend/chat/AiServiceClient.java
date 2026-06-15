package com.faraday.backend.chat;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;

import java.util.List;
import java.util.Map;

@Service
public class AiServiceClient {

    private final WebClient webClient;

    public AiServiceClient(@Value("${faraday.ai.base-url}") String baseUrl) {
        this.webClient = WebClient.builder()
                .baseUrl(baseUrl)
                .codecs(c -> c.defaultCodecs().maxInMemorySize(2 * 1024 * 1024))
                .build();
    }

    public Flux<ServerSentEvent<String>> streamChat(String query, List<String> ownerIds) {
        ParameterizedTypeReference<ServerSentEvent<String>> type =
                new ParameterizedTypeReference<>() {};
        return webClient.post()
                .uri("/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(Map.of("query", query, "owner_ids", ownerIds))
                .retrieve()
                .bodyToFlux(type);
    }
}
